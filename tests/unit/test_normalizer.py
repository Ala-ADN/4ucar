"""Unit tests for the value normalizer."""

import pytest

from backend.services.ingestion_service.normalizer import _normalize_value, normalize_row


def test_percentage_stripping():
    val, transforms = _normalize_value("75 %", "success_rate", "percentage")
    assert val == 75.0
    assert "percent_sign_stripped" in transforms


def test_french_decimal_comma():
    val, transforms = _normalize_value("75,5", "success_rate", "percentage")
    assert val == 75.5
    assert "comma_decimal_to_dot" in transforms


def test_french_thousands_separator():
    val, transforms = _normalize_value("1 200", "enrollment_total", "integer")
    assert val == 1200
    assert "thousands_separator_removed" in transforms


def test_arabic_indic_numerals():
    val, transforms = _normalize_value("٧٥", "success_rate", "percentage")
    assert val == 75.0
    assert "arabic_indic_to_western" in transforms


def test_currency_stripped():
    val, transforms = _normalize_value("500 000 TND", "budget_allocated", "float")
    assert val == 500000.0
    assert "currency_stripped" in transforms


def test_null_like_values():
    for null_str in ("", "N/A", "—", "nd", "nr", "-", "n/d", "non renseigné"):
        val, transforms = _normalize_value(null_str, "success_rate", "percentage")
        assert val is None
        assert "null_coerced" in transforms


def test_invalid_non_numeric():
    val, transforms = _normalize_value("texte invalide", "success_rate", "percentage")
    assert val is None
    assert "parse_failed" in transforms


def test_normalize_row():
    mapping = {
        "Taux de réussite": "success_rate",
        "Taux d'abandon": "dropout_rate",
        "Effectif total": "enrollment_total",
        "Colonne inconnue": None,
    }
    raw = {
        "Taux de réussite": "75,5 %",
        "Taux d'abandon": "10,2",
        "Effectif total": "1 200",
        "Colonne inconnue": "data",
    }
    normalized, log = normalize_row(raw, mapping)

    assert normalized["success_rate"] == 75.5
    assert normalized["dropout_rate"] == 10.2
    assert normalized["enrollment_total"] == 1200
    assert "Colonne inconnue" not in normalized
    assert len(log) > 0
