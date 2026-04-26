"""Unit tests for all validation rules."""

import pytest

from backend.services.ingestion_service.validator import ValidationStatus, validate_row


# ── Universal rules ───────────────────────────────────────────────────────────


def test_percentage_out_of_range_is_invalid():
    normalized = {"success_rate": 105.0, "dropout_rate": 10.0, "repetition_rate": 5.0, "enrollment_total": 100}
    mapping = {h: h for h in normalized}
    status, reason, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.INVALID
    assert field == "success_rate"


def test_negative_count_is_invalid():
    normalized = {
        "enrollment_total": 100,
        "teaching_staff_count": -1,
        "success_rate": 75.0,
        "dropout_rate": 10.0,
        "repetition_rate": 10.0,
    }
    mapping = {h: h for h in normalized}
    status, reason, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.INVALID
    assert field == "teaching_staff_count"


# ── Academic rules ────────────────────────────────────────────────────────────


def test_rate_sum_over_100_is_invalid():
    normalized = {
        "success_rate": 60.0,
        "dropout_rate": 25.0,
        "repetition_rate": 20.0,  # sum = 105
        "enrollment_total": 500,
    }
    mapping = {h: h for h in normalized}
    status, reason, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.INVALID
    assert "100%" in reason


def test_rate_sum_below_90_is_warned():
    normalized = {
        "success_rate": 60.0,
        "dropout_rate": 10.0,
        "repetition_rate": 10.0,  # sum = 80 < 90
        "enrollment_total": 500,
    }
    mapping = {h: h for h in normalized}
    status, reason, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.WARNED
    assert "90%" in reason


def test_success_rate_100_is_warned():
    normalized = {
        "success_rate": 100.0,
        "dropout_rate": 0.0,
        "repetition_rate": 0.0,
        "enrollment_total": 500,
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.WARNED
    assert field == "success_rate"


def test_success_rate_below_20_is_warned():
    normalized = {
        "success_rate": 15.0,
        "dropout_rate": 50.0,
        "repetition_rate": 35.0,
        "enrollment_total": 500,
    }
    mapping = {h: h for h in normalized}
    status, _, _ = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.WARNED


def test_high_str_is_warned():
    normalized = {
        "success_rate": 75.0,
        "dropout_rate": 10.0,
        "repetition_rate": 10.0,
        "enrollment_total": 500,
        "student_teacher_ratio": 90.0,
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.WARNED
    assert field == "student_teacher_ratio"


def test_valid_academic_row():
    normalized = {
        "success_rate": 75.0,
        "dropout_rate": 10.0,
        "repetition_rate": 10.0,
        "enrollment_total": 500,
    }
    mapping = {h: h for h in normalized}
    status, _, _ = validate_row(normalized, mapping, "academic")
    assert status == ValidationStatus.VALID


# ── Financial rules ───────────────────────────────────────────────────────────


def test_budget_overrun_over_20pct_is_invalid():
    normalized = {
        "budget_allocated": 100000.0,
        "budget_consumed": 125000.0,  # 25% overrun
    }
    mapping = {h: h for h in normalized}
    status, reason, field = validate_row(normalized, mapping, "finance")
    assert status == ValidationStatus.INVALID
    assert field == "budget_consumed"


def test_budget_overrun_under_20pct_is_warned():
    normalized = {
        "budget_allocated": 100000.0,
        "budget_consumed": 110000.0,  # 10% overrun — warned
    }
    mapping = {h: h for h in normalized}
    status, _, _ = validate_row(normalized, mapping, "finance")
    assert status == ValidationStatus.WARNED


def test_budget_execution_rate_mismatch_is_warned():
    normalized = {
        "budget_allocated": 100000.0,
        "budget_consumed": 80000.0,
        "budget_execution_rate": 90.0,  # computed = 80%, declared = 90% → diff = 10 > 5
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "finance")
    assert status == ValidationStatus.WARNED
    assert field == "budget_execution_rate"


# ── Operational rules ─────────────────────────────────────────────────────────


def test_zero_teaching_staff_is_invalid():
    normalized = {
        "teaching_staff_count": 0,
        "admin_staff_count": 5,
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "operational")
    assert status == ValidationStatus.INVALID
    assert field == "teaching_staff_count"


def test_admin_over_3x_teaching_is_warned():
    normalized = {
        "teaching_staff_count": 10,
        "admin_staff_count": 35,  # 3.5× teaching
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "operational")
    assert status == ValidationStatus.WARNED
    assert field == "admin_staff_count"


def test_high_absenteeism_is_warned():
    normalized = {
        "teaching_staff_count": 20,
        "absenteeism_rate": 55.0,
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "operational")
    assert status == ValidationStatus.WARNED
    assert field == "absenteeism_rate"


# ── Environmental rules ───────────────────────────────────────────────────────


def test_zero_energy_is_warned():
    normalized = {
        "energy_kwh": 0.0,
    }
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "environmental")
    assert status == ValidationStatus.WARNED
    assert field == "energy_kwh"


def test_energy_spike_is_warned():
    normalized = {"energy_kwh": 310000.0}
    previous = {"energy_kwh": 100000.0}  # 210% increase
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "environmental", previous=previous)
    assert status == ValidationStatus.WARNED
    assert field == "energy_kwh"


# ── Cross-period rules ────────────────────────────────────────────────────────


def test_large_enrollment_delta_is_warned():
    normalized = {
        "enrollment_total": 1500,
        "success_rate": 75.0,
        "dropout_rate": 10.0,
        "repetition_rate": 10.0,
    }
    previous = {"enrollment_total": 1000}  # 50% change > 20% threshold
    mapping = {h: h for h in normalized}
    status, _, field = validate_row(normalized, mapping, "academic", previous=previous)
    assert status == ValidationStatus.WARNED
    assert field == "enrollment_total"
