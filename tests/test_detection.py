
from unittest.mock import MagicMock

from src.detection import (
    RULES,
    create_indicator,
    detect_invalid_policy,
    detect_duplicate_invoices,
    detect_payment_overstatement,
    detect_shared_contacts,
    detect_invalid_provider_relationships,
)


def test_detection_functions_are_available():
    functions = [
        detect_invalid_policy,
        detect_duplicate_invoices,
        detect_payment_overstatement,
        detect_shared_contacts,
        detect_invalid_provider_relationships,
    ]

    assert len(functions) == 5
    assert all(callable(function) for function in functions)


def test_rule_configuration():
    assert RULES["INVALID_POLICY_REFERENCE"]["risk_score"] == 30.0
    assert RULES["DUPLICATE_INVOICE"]["risk_score"] == 25.0
    assert RULES["PAYMENT_OVERSTATEMENT"]["risk_score"] == 40.0
    assert RULES["SHARED_CONTACT_PATTERN"]["risk_score"] == 10.0
    assert RULES["INVALID_PROVIDER_RELATIONSHIP"]["risk_score"] == 25.0


def test_create_indicator():
    indicator = create_indicator(
        "TEST-001",
        "CLM-TEST-001",
        "PAYMENT_OVERSTATEMENT",
        "Payment exceeds approved amount",
    )

    assert indicator == (
        "TEST-001",
        "CLM-TEST-001",
        "PAYMENT_OVERSTATEMENT",
        "Payment exceeds approved amount",
        "CRITICAL",
        40.0,
    )


def test_invalid_policy_detection():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("CLM-TEST-001", "POL-INVALID-001", "Invalid policy reference")
    ]

    results = detect_invalid_policy(cursor)

    assert len(results) == 1
    assert results[0][1] == "CLM-TEST-001"
    assert results[0][2] == "INVALID_POLICY_REFERENCE"
    assert results[0][4] == "HIGH"


def test_duplicate_invoice_detection():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        (101, "INV-TEST-001", "CLM-TEST-001", 5000.00),
        (102, "INV-TEST-001", "CLM-TEST-002", 5000.00),
    ]

    results = detect_duplicate_invoices(cursor)

    assert len(results) == 2
    assert all(
        result[2] == "DUPLICATE_INVOICE"
        for result in results
    )
    assert all(result[4] == "HIGH" for result in results)


def test_payment_overstatement_detection():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("PAY-TEST-001", "CLM-TEST-001", 12000.00, 10000.00)
    ]

    results = detect_payment_overstatement(cursor)

    assert len(results) == 1
    assert results[0][1] == "CLM-TEST-001"
    assert results[0][2] == "PAYMENT_OVERSTATEMENT"
    assert "2000.00" in results[0][3]
    assert results[0][4] == "CRITICAL"


def test_shared_contact_detection():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("CTM-TEST-001", "9999999999", "CLM-TEST-001", 4)
    ]

    results = detect_shared_contacts(cursor)

    assert len(results) == 1
    assert results[0][1] == "CLM-TEST-001"
    assert results[0][2] == "SHARED_CONTACT_PATTERN"
    assert results[0][4] == "MEDIUM"
    assert "not proof of fraud" in results[0][3]


def test_invalid_provider_relationship_detection():
    cursor = MagicMock()
    cursor.fetchall.return_value = [
        ("EDGE-TEST-001", "CLM-TEST-001", "PRV-MISSING-001")
    ]

    results = detect_invalid_provider_relationships(cursor)

    assert len(results) == 1
    assert results[0][1] == "CLM-TEST-001"
    assert results[0][2] == "INVALID_PROVIDER_RELATIONSHIP"
    assert results[0][4] == "HIGH"


def test_detection_functions_return_empty_results():
    detection_functions = [
        detect_invalid_policy,
        detect_duplicate_invoices,
        detect_payment_overstatement,
        detect_shared_contacts,
        detect_invalid_provider_relationships,
    ]

    for detection_function in detection_functions:
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        results = detection_function(cursor)

        assert results == []
