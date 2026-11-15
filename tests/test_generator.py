
from unittest.mock import MagicMock, patch

import pytest

from src import generator


def test_get_table_count():
    cursor = MagicMock()
    cursor.fetchone.return_value = (2000,)

    result = generator.get_table_count(cursor, "claimants")

    assert result == 2000
    cursor.execute.assert_called_once_with(
        "SELECT COUNT(*) FROM claimants"
    )


def test_get_table_count_rejects_invalid_table():
    cursor = MagicMock()

    with pytest.raises(ValueError, match="Invalid table name"):
        generator.get_table_count(cursor, "users")

    cursor.execute.assert_not_called()


def test_insert_records():
    cursor = MagicMock()

    rows = [
        ("CTM-TEST-001", "Test Claimant"),
        ("CTM-TEST-002", "Test Claimant 2"),
    ]

    generator.insert_records(
        cursor,
        "INSERT INTO test_table VALUES (%s, %s)",
        rows,
    )

    cursor.executemany.assert_called_once_with(
        "INSERT INTO test_table VALUES (%s, %s)",
        rows,
    )


def test_generate_claimants():
    rows = generator.generate_claimants()

    assert len(rows) == generator.TOTAL_CLAIMANTS
    assert len(rows[0]) == 8

    assert rows[0][0] == "CTM-2026-000001"
    assert rows[-1][0] == (
        f"CTM-2026-{generator.TOTAL_CLAIMANTS:06d}"
    )

    for row in rows:
        assert 18 <= row[2] <= 85
        assert row[3] in ["Male", "Female", "Other"]
        assert row[7].endswith("@example.com")


def test_generate_providers():
    rows = generator.generate_providers()

    assert len(rows) == generator.TOTAL_PROVIDERS
    assert len(rows[0]) == 6

    assert rows[0][0] == "PRV-000001"

    allowed_types = {
        "Hospital",
        "Vehicle Repair",
        "Diagnostic Center",
        "Pharmacy",
        "Legal Service",
    }

    for row in rows:
        assert row[2] in allowed_types


def test_generate_policies():
    rows = generator.generate_policies()

    assert len(rows) == generator.TOTAL_POLICIES
    assert len(rows[0]) == 8

    assert rows[0][0] == "POL-2026-000001"
    assert rows[0][1] == "CTM-2026-000001"

    for row in rows:
        assert row[5] > 0
        assert row[6] > 0
        assert row[7] in ["Active", "Expired"]


def test_generate_incidents():
    rows = generator.generate_incidents()

    assert len(rows) == generator.TOTAL_INCIDENTS
    assert len(rows[0]) == 6

    assert rows[0][0] == "INC-2026-000001"

    for row in rows:
        assert row[5] >= 10000
        assert row[2] is not None


def test_generate_claimants_respects_configured_count():
    with patch.object(generator, "TOTAL_CLAIMANTS", 3):
        rows = generator.generate_claimants()

    assert len(rows) == 3


def test_generate_providers_respects_configured_count():
    with patch.object(generator, "TOTAL_PROVIDERS", 3):
        rows = generator.generate_providers()

    assert len(rows) == 3


def test_generate_policies_respects_configured_count():
    with patch.object(generator, "TOTAL_POLICIES", 3):
        rows = generator.generate_policies()

    assert len(rows) == 3


def test_generate_incidents_respects_configured_count():
    with patch.object(generator, "TOTAL_INCIDENTS", 3):
        rows = generator.generate_incidents()

    assert len(rows) == 3
