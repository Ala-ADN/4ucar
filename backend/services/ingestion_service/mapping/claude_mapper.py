"""Column-to-field mapping via Claude API.

PROTOTYPE ONLY — Claude API used for column mapping demo purposes.
Production replacement: intfloat/multilingual-e5-large sentence embeddings
running locally on UCAR servers. Pre-compute embeddings for all KPI field
aliases at startup. At mapping time, encode column header and find nearest
neighbor by cosine similarity. Zero external calls, full data sovereignty.
Ollama + Mistral 7B as secondary fallback for ambiguous cases.
No code changes required in callers — same interface, different implementation.

What is sent to Claude:
  - Only the list of extracted column header strings
  - The list of target KPI fields for the declared domain (labels + aliases)
  NO row data. NO values. NO student records. NO institutional identifiers.
  Column headers are the only content that ever leaves the server.
"""

import json

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from backend.services.ingestion_service.config import get_settings
from backend.services.ingestion_service.kpi_schema import KPI_FIELDS, fields_for_domain
from backend.shared.logging import get_logger

logger = get_logger(__name__)

_SYSTEM_PROMPT = """Tu es un assistant de correspondance de données pour un système de gestion universitaire.
Ta tâche est de faire correspondre des en-têtes de colonnes d'un fichier à des champs cibles d'une base de données KPI universitaire.
Réponds uniquement avec un tableau JSON. Aucune explication supplémentaire.
"""


def propose_mapping(headers: list[str], domain: str) -> list[dict]:
    """Call Claude to propose column→field mappings.

    Returns a list of dicts:
    [
        {"column": "Taux de réussite", "field_id": "success_rate", "confidence": 0.95, "reason": "..."},
        {"column": "Inconnu", "field_id": null, "confidence": 0.0, "reason": "Aucune correspondance trouvée."},
    ]
    """
    settings = get_settings()
    domain_fields = fields_for_domain(domain)  # type: ignore[arg-type]

    fields_description = "\n".join(
        f"- {fid}: {f.label_fr} (aliases: {', '.join(f.aliases[:5])})"
        for fid, f in domain_fields.items()
    )

    user_prompt = f"""En-têtes de colonnes à correspondre :
{json.dumps(headers, ensure_ascii=False, indent=2)}

Champs cibles disponibles (domaine : {domain}) :
{fields_description}

Renvoie un tableau JSON où chaque élément a :
  - "column": l'en-tête d'origine (chaîne exacte)
  - "field_id": l'identifiant du champ cible, ou null si aucune correspondance
  - "confidence": score de confiance entre 0.0 et 1.0
  - "reason": une phrase expliquant la décision

Exemple de format :
[
  {{"column": "Taux de réussite", "field_id": "success_rate", "confidence": 0.97, "reason": "Correspondance directe avec le label français."}},
  {{"column": "Données inconnues", "field_id": null, "confidence": 0.0, "reason": "Aucune correspondance trouvée dans le schéma."}}
]"""

    raw = _call_claude(
        system=_SYSTEM_PROMPT,
        user=user_prompt,
        timeout=settings.claude_timeout_seconds,
        max_retries=settings.claude_max_retries,
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
    )

    parsed = _parse_and_validate(raw, set(KPI_FIELDS.keys()))
    return parsed


@retry(
    retry=retry_if_exception_type((anthropic.APITimeoutError, anthropic.APIConnectionError)),
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
)
def _call_claude(
    system: str,
    user: str,
    timeout: int,
    max_retries: int,
    api_key: str,
    model: str,
) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
        timeout=timeout,
    )
    return message.content[0].text


def _parse_and_validate(raw: str, valid_field_ids: set[str]) -> list[dict]:
    """Parse JSON response and discard any mapping referencing non-existent field IDs."""
    # Strip markdown code fences if present
    clean = raw.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
    if clean.endswith("```"):
        clean = "\n".join(clean.split("\n")[:-1])

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned invalid JSON: {exc}") from exc

    if not isinstance(data, list):
        raise ValueError("Claude response is not a JSON array")

    validated = []
    for item in data:
        if not isinstance(item, dict) or "column" not in item:
            continue
        field_id = item.get("field_id")
        # Discard if field_id is non-null and not in the known schema
        if field_id is not None and field_id not in valid_field_ids:
            logger.warning("claude_invented_field_id", field_id=field_id)
            item["field_id"] = None
            item["confidence"] = 0.0
            item["reason"] = "Identifiant de champ inconnu — ignoré."
        validated.append(item)

    return validated
