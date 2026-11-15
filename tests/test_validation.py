
from unittest.mock import MagicMock, call

from src.validation import (
    EXPECTED_COUNTS,
    get_count,
    print_result,
    validate_record_counts,
    validate_claim_references,
    validate_duplicate_invoices,
    validate_payment_amounts,
    validate_shared_contacts,
    validate_provider_relationships,
    validate_quality_issue_records,
)


def test_expected_dataset_counts():
    assert EXPECTED_COUNTS["claimants"] == 2000
    assert EXPECTED_COUNTS["policies"] == 2000
    assert EXPECTED_COUNTS["claims"] == 5000
    assert EXPECTED_COUNTS["providers"] == 500
    assert EXPECTED_COUNTS["relationship_edges"] == 8000


def test_get_count_returns_database_count():
    cursor = MagicMock()
    cursor.fetchone.return_value = (2000,)

    result = get_count(cursor, "SELECT COUNT(*) FROM claimants")

    assert result == 2000


def test_get_count_returns_zero_when_result_is_empty():
    cursor = MagicMock()
    cursor.fetchone.return_value = None

    result = get_count(cursor, "SELECT COUNT(*) FROM claimants")

    assert result == 0


def test_print_result_pass(capsys):
    print_result("claimants", 2000, 2000)

    output = capsys.readouterr().out

    assert "[PASS]" in output
    assert "claimants: 2000" in output


def test_print_result_warning(capsys):
    print_result("claimants", 1900, 2000)

    output = capsys.readouterr().out

    assert "[WARNING]" in output
    assert "Found 1900" in output


def test_print_result_info(capsys):
    print_result("data quality issues", 1)

    output = capsys.readouterr().out

    assert "[INFO]" in output
    assert "data quality issues: 1" in output


def test_validate_record_counts(capsys):
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        (expected,) for expected in EXPECTED_COUNTS.values()
    ]

    validate_record_counts(cursor)

    output = capsys.readouterr().out

    assert output.count("[PASS]") == len(EXPECTED_COUNTS)
    assert output.count("[WARNING]") == 0


def test_validate_claim_references(capsys):
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        (0,), (0,), (1,), (0,)
    ]

    validate_claim_references(cursor)

    output = capsys.readouterr().out

    assert output.count("[PASS]") == 3
    assert "[WARNING] Claims with NULL policy reference: 1" in output


def test_validate_duplicate_invoices_warning(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    validate_duplicate_invoices(cursor)

    output = capsys.readouterr().out

    assert "Duplicate invoice groups detected: 1" in output


def test_validate_duplicate_invoices_pass(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (0,)

    validate_duplicate_invoices(cursor)

    output = capsys.readouterr().out

    assert "No duplicate invoice numbers found." in output


def test_validate_payment_amounts_warning(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    validate_payment_amounts(cursor)

    output = capsys.readouterr().out

    assert "Payments exceeding approved amounts: 1" in output


def test_validate_shared_contacts_warning(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    validate_shared_contacts(cursor)

    output = capsys.readouterr().out

    assert "Shared phone number groups detected: 1" in output


def test_validate_provider_relationships_warning(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    validate_provider_relationships(cursor)

    output = capsys.readouterr().out

    assert "Invalid provider relationships: 1" in output


def test_validate_quality_issue_records(capsys):
    cursor = MagicMock()
    cursor.fetchone.return_value = (1,)

    validate_quality_issue_records(cursor)

    output = capsys.readouterr().out

    assert "[INFO] Recorded data quality issues: 1" in output
