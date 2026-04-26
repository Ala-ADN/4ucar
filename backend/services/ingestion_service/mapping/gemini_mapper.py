"""Column-to-field mapping via Google Gemini API.

# PROTOTYPE ONLY — Gemini API used for column mapping demo purposes.
# Production replacement: intfloat/multilingual-e5-large sentence embeddings
# running locally on UCAR servers via sentence-transformers library.
# Pre-compute embeddings for all KPI field aliases at startup.
# At mapping time: encode column header → cosine similarity → nearest neighbor.
# Secondary fallback: Ollama + Mistral 7B for ambiguous cases.
# Zero external API calls, full data sovereignty, sub-millisecond mapping.
# Swap implementation here — callers do not change.

What is sent to Gemini:
  - Only the list of extracted column header strings
  - The list of target KPI fields for the declared domain (labels + aliases)
  NO row data. NO values. NO student records. NO institutional identifiers.
  Column headers are the only content that ever leaves the server.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import time

import redis as sync_redis

from backend.services.ingestion_service.kpi_schema import KPI_FIELDS, build_alias_map, fields_for_domain
from backend.services.ingestion_service.mapping.fuzzy_mapper import fuzzy_map
from backend.shared.logging import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = (
    "You are a precise data mapping assistant for a university management system "
    "used by the University of Carthage, Tunisia. Your task is to map column headers "
    "from uploaded institutional data files to canonical KPI field identifiers. "
    "Column headers may be in French, Arabic, or abbreviated forms. "
    "You must return only a valid JSON array with no surrounding text."
)

_GEMINI_CLIENT = None
_ALIAS_MAP: dict[str, str] | None = None
_REDIS_CLIENT: sync_redis.Redis | None = None


def _get_gemini_client(api_key: str):
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is None:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        _GEMINI_CLIENT = genai
    return _GEMINI_CLIENT


def _get_redis(url: str) -> sync_redis.Redis:
    global _REDIS_CLIENT
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = sync_redis.from_url(url, decode_responses=True)
    return _REDIS_CLIENT


def _cache_key(domain: str, headers: list[str]) -> str:
    fingerprint = json.dumps(sorted(headers), ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(fingerprint.encode()).hexdigest()
    return f"mapping:{domain}:{digest}"


def _build_user_prompt(headers: list[str], domain: str) -> str:
    domain_fields = fields_for_domain(domain)  # type: ignore[arg-type]
    fields_block = "\n".join(
        f'- identifier: "{fid}"\n  label: "{f.label_fr}"\n  aliases: {json.dumps(f.aliases[:8], ensure_ascii=False)}'
        for fid, f in domain_fields.items()
    )
    return (
        f"Domain: {domain}\n\n"
        f"Input column headers:\n{json.dumps(headers, ensure_ascii=False, indent=2)}\n\n"
        f"Available target fields:\n{fields_block}\n\n"
        "Return a JSON array where each element is:\n"
        '{"original_column": "exact string from input", '
        '"platform_field": "field_identifier or null", '
        '"confidence": 0.95, '
        '"reasoning": "one sentence in French explaining the match"}\n\n'
        "Rules:\n"
        "- Every input column must appear exactly once in the output\n"
        "- platform_field must be one of the provided identifiers, or null\n"
        "- Do not invent field identifiers\n"
        "- If multiple columns map to the same field, keep the best match and set others to null\n"
        "- confidence 1.0 = certain, 0.0 = no match"
    )


def _call_gemini(prompt: str, api_key: str, model: str, timeout: int) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": 0,
        "response_mime_type": "application/json",
    }
    gemini_model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
        system_instruction=_SYSTEM_PROMPT,
    )
    response = gemini_model.generate_content(prompt, request_options={"timeout": timeout})
    return response.text


def _parse_and_validate(raw: str, headers: list[str], domain: str) -> list[dict]:
    """Parse Gemini JSON response and validate all field IDs against the schema."""
    valid_field_ids = set(KPI_FIELDS.keys())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Gemini returned invalid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Gemini response is not a JSON array")

    # Normalize key names — prompt uses original_column/platform_field/reasoning
    result_by_column: dict[str, dict] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        column = item.get("original_column") or item.get("column", "")
        field_id = item.get("platform_field") or item.get("field_id")
        confidence = float(item.get("confidence", 0.0))
        reason = item.get("reasoning") or item.get("reason", "")

        if field_id is not None and field_id not in valid_field_ids:
            logger.warning("gemini_invented_field_id", field_id=field_id)
            field_id = None
            confidence = 0.0
            reason = "Identifiant de champ inconnu — ignoré."

        result_by_column[column] = {
            "column": column,
            "field_id": field_id,
            "confidence": confidence,
            "reason": reason,
        }

    # Ensure every input column appears in output
    output = []
    for header in headers:
        if header in result_by_column:
            output.append(result_by_column[header])
        else:
            output.append({
                "column": header,
                "field_id": None,
                "confidence": 0.0,
                "reason": "Colonne absente de la réponse Gemini.",
            })

    return output


def propose_mapping(headers: list[str], domain: str) -> list[dict]:
    """Map column headers to KPI fields using Gemini with Redis cache and fuzzy fallback.

    Returns a list of dicts (same format as claude_mapper.propose_mapping):
    [{"column": str, "field_id": str|None, "confidence": float, "reason": str}]
    """
    from backend.services.ingestion_service.config import get_settings
    settings = get_settings()

    redis_url = settings.redis_url
    api_key = settings.gemini_api_key
    model = settings.gemini_model
    timeout = settings.gemini_timeout_seconds
    cache_ttl = settings.mapping_cache_ttl_seconds

    # ── Cache lookup ──────────────────────────────────────────────────────────
    try:
        r = _get_redis(redis_url)
        key = _cache_key(domain, headers)
        cached = r.get(key)
        if cached:
            logger.info("mapping_cache_hit", domain=domain, key=key)
            return json.loads(cached)
    except Exception as exc:
        logger.warning("mapping_cache_read_failed", error=str(exc))

    # ── Gemini call with one retry ────────────────────────────────────────────
    user_prompt = _build_user_prompt(headers, domain)
    result: list[dict] | None = None

    for attempt in range(2):
        try:
            raw = _call_gemini(user_prompt, api_key=api_key, model=model, timeout=timeout)
            result = _parse_and_validate(raw, headers, domain)
            break
        except Exception as exc:
            logger.warning("gemini_mapping_attempt_failed", attempt=attempt + 1, error=str(exc))
            if attempt == 0:
                time.sleep(2)

    # ── Fuzzy fallback ────────────────────────────────────────────────────────
    if result is None:
        logger.info("gemini_mapping_falling_back_to_fuzzy", domain=domain)
        return fuzzy_map(headers, domain)

    # ── Cache store (Gemini results only, avg confidence ≥ 0.5) ──────────────
    avg_conf = sum(r["confidence"] for r in result) / len(result) if result else 0.0
    if avg_conf >= 0.5:
        try:
            r = _get_redis(redis_url)
            r.setex(key, cache_ttl, json.dumps(result, ensure_ascii=False))
        except Exception as exc:
            logger.warning("mapping_cache_write_failed", error=str(exc))

    return result
