"""Business rule validation — Stage 6 of the ingestion pipeline.

Classifies each normalized row as: valid | warned | invalid.
Invalid rows go to quarantine. Warned rows are committed with a flag.

Rules implemented (full spec from the build prompt):
  Universal: percentage 0–100, counts ≥ 0, required non-null, type-correct
  Academic:  rate sum, suspicious outliers, STR, attendance
  Financial: budget overrun, cross-check declared vs computed rate
  Operational: teaching_staff=0, admin ratio, absenteeism
  Environmental: energy=0, month-over-month spike
  Cross-period: large delta warnings (caller must supply previous values)
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from backend.services.ingestion_service.kpi_schema import KPI_FIELDS, required_fields_for_domain


class ValidationStatus(StrEnum):
    VALID = "valid"
    WARNED = "warned"
    INVALID = "invalid"


def validate_row(
    normalized: dict[str, Any],
    mapping: dict[str, str | None],
    domain: str,
    previous: dict[str, Any] | None = None,
) -> tuple[ValidationStatus, str | None, str | None]:
    """Validate one normalized row.

    Returns (status, reason_fr, failed_field_id).
    On VALID status, reason and field are None.
    """
    # ── Universal rules ──────────────────────────────────────────────────────
    for field_id, value in normalized.items():
        kpi = KPI_FIELDS.get(field_id)
        if kpi is None:
            continue

        if value is None:
            if kpi.required:
                return ValidationStatus.INVALID, f"Le champ obligatoire « {kpi.label_fr} » est absent.", field_id
            continue

        if kpi.data_type in ("float", "percentage", "integer") and not isinstance(value, (int, float)):
            return ValidationStatus.INVALID, f"La valeur du champ « {kpi.label_fr} » n'est pas numérique.", field_id

        if kpi.data_type == "percentage":
            if not (0 <= float(value) <= 100):
                return ValidationStatus.INVALID, (
                    f"Le taux « {kpi.label_fr} » ({value}) est hors de l'intervalle 0–100."
                ), field_id

        if kpi.data_type in ("integer", "float") and isinstance(value, (int, float)):
            if value < 0:
                return ValidationStatus.INVALID, (
                    f"Le champ « {kpi.label_fr} » ({value}) ne peut pas être négatif."
                ), field_id

    # ── Required fields check ────────────────────────────────────────────────
    for req_field in required_fields_for_domain(domain):  # type: ignore[arg-type]
        if req_field not in normalized or normalized[req_field] is None:
            kpi = KPI_FIELDS.get(req_field)
            label = kpi.label_fr if kpi else req_field
            return ValidationStatus.INVALID, f"Le champ obligatoire « {label} » est absent ou nul.", req_field

    # ── Domain-specific rules ────────────────────────────────────────────────
    if domain == "academic":
        result = _validate_academic(normalized)
        if result:
            return result

    elif domain == "finance":
        result = _validate_finance(normalized)
        if result:
            return result

    elif domain == "operational":
        result = _validate_operational(normalized)
        if result:
            return result

    elif domain == "environmental":
        result = _validate_environmental(normalized, previous)
        if result:
            return result

    # ── Cross-period consistency ─────────────────────────────────────────────
    if previous:
        result = _validate_cross_period(normalized, previous, domain)
        if result:
            return result

    return ValidationStatus.VALID, None, None


# ── Academic ─────────────────────────────────────────────────────────────────


def _validate_academic(n: dict) -> tuple[ValidationStatus, str, str] | None:
    success = n.get("success_rate")
    dropout = n.get("dropout_rate")
    repetition = n.get("repetition_rate")
    str_val = n.get("student_teacher_ratio")
    attendance = n.get("attendance_rate")

    if success is not None and dropout is not None and repetition is not None:
        total = float(success) + float(dropout) + float(repetition)
        if total > 100:
            return ValidationStatus.INVALID, (
                f"La somme réussite+abandon+redoublement ({total:.1f}%) dépasse 100% — données incohérentes."
            ), "success_rate"
        if total < 90:
            return ValidationStatus.WARNED, (
                f"La somme réussite+abandon+redoublement ({total:.1f}%) est inférieure à 90% — étudiants non comptabilisés."
            ), "success_rate"

    if success is not None:
        s = float(success)
        if s == 100:
            return ValidationStatus.WARNED, "Taux de réussite de 100% — valeur suspecte à vérifier.", "success_rate"
        if s < 20:
            return ValidationStatus.WARNED, f"Taux de réussite très faible ({s}%) — valeur suspecte.", "success_rate"

    if str_val is not None and float(str_val) > 80:
        return ValidationStatus.WARNED, (
            f"Ratio étudiants/enseignants élevé ({str_val}) — dépassement du seuil d'alerte de 80."
        ), "student_teacher_ratio"

    if attendance is not None and float(attendance) < 30:
        return ValidationStatus.WARNED, (
            f"Taux de présence très faible ({attendance}%) — à vérifier."
        ), "attendance_rate"

    return None


# ── Finance ───────────────────────────────────────────────────────────────────


def _validate_finance(n: dict) -> tuple[ValidationStatus, str, str] | None:
    allocated = n.get("budget_allocated")
    consumed = n.get("budget_consumed")
    declared_rate = n.get("budget_execution_rate")

    if allocated is not None and consumed is not None:
        a, c = float(allocated), float(consumed)
        if a > 0:
            ratio = c / a
            if ratio > 1.20:
                return ValidationStatus.INVALID, (
                    f"Le budget consommé ({c:,.0f}) dépasse de plus de 20% le budget alloué ({a:,.0f})."
                ), "budget_consumed"
            if ratio > 1.0:
                return ValidationStatus.WARNED, (
                    f"Le budget consommé ({c:,.0f}) dépasse légèrement le budget alloué ({a:,.0f})."
                ), "budget_consumed"

            # Cross-check declared execution rate vs computed
            if declared_rate is not None:
                computed_rate = (c / a) * 100
                if abs(computed_rate - float(declared_rate)) > 5:
                    return ValidationStatus.WARNED, (
                        f"Le taux d'exécution déclaré ({declared_rate}%) diffère du taux calculé "
                        f"({computed_rate:.1f}%) de plus de 5 points."
                    ), "budget_execution_rate"

    return None


# ── Operational ───────────────────────────────────────────────────────────────


def _validate_operational(n: dict) -> tuple[ValidationStatus, str, str] | None:
    teaching = n.get("teaching_staff_count")
    admin = n.get("admin_staff_count")
    absenteeism = n.get("absenteeism_rate")

    if teaching is not None and int(teaching) == 0:
        return ValidationStatus.INVALID, (
            "Le nombre d'enseignants ne peut pas être zéro — aucun établissement ne fonctionne sans enseignants."
        ), "teaching_staff_count"

    if teaching and admin:
        t, a = int(teaching), int(admin)
        if t > 0 and a > 3 * t:
            return ValidationStatus.WARNED, (
                f"Le personnel administratif ({a}) représente plus de 3× les enseignants ({t}) — valeur suspecte."
            ), "admin_staff_count"

    if absenteeism is not None and float(absenteeism) > 50:
        return ValidationStatus.WARNED, (
            f"Taux d'absentéisme très élevé ({absenteeism}%) — à vérifier."
        ), "absenteeism_rate"

    return None


# ── Environmental ─────────────────────────────────────────────────────────────


def _validate_environmental(
    n: dict, previous: dict | None
) -> tuple[ValidationStatus, str, str] | None:
    energy = n.get("energy_kwh")

    if energy is not None and float(energy) == 0:
        return ValidationStatus.WARNED, (
            "La consommation d'énergie est à zéro — données probablement manquantes."
        ), "energy_kwh"

    if previous and energy is not None:
        prev_energy = previous.get("energy_kwh")
        if prev_energy and float(prev_energy) > 0:
            change_pct = ((float(energy) - float(prev_energy)) / float(prev_energy)) * 100
            if change_pct > 200:
                return ValidationStatus.WARNED, (
                    f"Augmentation de la consommation d'énergie de {change_pct:.0f}% par rapport à la période précédente — à vérifier."
                ), "energy_kwh"

    return None


# ── Cross-period consistency ──────────────────────────────────────────────────


def _validate_cross_period(
    n: dict, previous: dict, domain: str
) -> tuple[ValidationStatus, str, str] | None:
    checks = [
        ("success_rate", 15, "Le taux de réussite"),
        ("dropout_rate", 10, "Le taux d'abandon"),
        ("enrollment_total", 20, "L'effectif total"),
    ]

    for field_id, threshold, label in checks:
        current = n.get(field_id)
        prev = previous.get(field_id)
        if current is None or prev is None or float(prev) == 0:
            continue
        delta = abs(float(current) - float(prev)) / float(prev) * 100
        if delta > threshold:
            return ValidationStatus.WARNED, (
                f"{label} a varié de {delta:.1f}% par rapport à la période précédente — variation inhabituelle."
            ), field_id

    if domain == "finance":
        current_budget = n.get("budget_allocated")
        prev_budget = previous.get("budget_allocated")
        if current_budget and prev_budget and float(prev_budget) > 0:
            delta = abs(float(current_budget) - float(prev_budget)) / float(prev_budget) * 100
            if delta > 30:
                return ValidationStatus.WARNED, (
                    f"Le budget alloué a varié de {delta:.1f}% par rapport à l'année précédente — variation inhabituelle."
                ), "budget_allocated"

    return None
