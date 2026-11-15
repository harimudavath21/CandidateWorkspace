
import csv
from pathlib import Path

from config import DATA_DIR
from src.storage import get_connection


# =====================================================
# 1. CONFIGURATION
# =====================================================

GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"

INVALID_CLAIM_ID = "CLM-2026-000101"
OVERPAYMENT_CLAIM_ID = "CLM-2026-000202"
INCORRECT_EDGE_CLAIM_ID = "CLM-2026-000250"

SHARED_PHONE = "9999999999"

GROUND_TRUTH_COLUMNS = [
    "anomaly_id",
    "entity_type",
    "entity_id",
    "anomaly_type",
    "expected_label",
    "description",
]


# =====================================================
# 2. HELPER: ADD GROUND TRUTH RECORD
# =====================================================

def add_ground_truth(
    records,
    anomaly_id,
    entity_type,
    entity_id,
    anomaly_type,
    description,
):
    records.append({
        "anomaly_id": anomaly_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "anomaly_type": anomaly_type,
        "expected_label": "SUSPICIOUS",
        "description": description,
    })


# =====================================================
# 3. INVALID POLICY REFERENCE
# =====================================================

def inject_invalid_policy(cursor, ground_truth):
    """
    Preserve an invalid policy reference in the data-quality
    exception table and set claims.policy_id to NULL.
    """

    cursor.execute("""
        SELECT policy_id
        FROM claims
        WHERE claim_id = %s
    """, (INVALID_CLAIM_ID,))

    result = cursor.fetchone()

    if result is None:
        raise ValueError("Target claim does not exist")

    original_policy_id = result[0]

    invalid_policy_id = "POL-INVALID-999999"

    cursor.execute("""
        UPDATE claims
        SET policy_id = NULL
        WHERE claim_id = %s
    """, (INVALID_CLAIM_ID,))

    cursor.execute("""
        INSERT INTO data_quality_issues (
            entity_type,
            entity_id,
            field_name,
            invalid_value,
            issue_type,
            issue_description,
            resolution_status
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        "CLAIM",
        INVALID_CLAIM_ID,
        "policy_id",
        invalid_policy_id,
        "INVALID_POLICY_REFERENCE",
        "Claim references a policy ID that does not exist.",
        "OPEN",
    ))

    add_ground_truth(
        ground_truth,
        "ANOM-001",
        "CLAIM",
        INVALID_CLAIM_ID,
        "INVALID_POLICY_REFERENCE",
        f"Invalid policy reference: {invalid_policy_id}. "
        f"Original policy was {original_policy_id}.",
    )


# =====================================================
# 4. DUPLICATE INVOICE
# =====================================================

def inject_duplicate_invoice(cursor, ground_truth):
    """Create a duplicate business invoice number."""

    cursor.execute("""
        SELECT invoice_record_id, invoice_id, claim_id
        FROM invoices
        ORDER BY invoice_record_id
        LIMIT 2
    """)

    invoices = cursor.fetchall()

    if len(invoices) != 2:
        raise ValueError("Two invoice records are required")

    first_invoice = invoices[0]
    second_invoice = invoices[1]

    if first_invoice[2] == second_invoice[2]:
        raise ValueError("Invoices must belong to different claims")

    duplicate_invoice_id = first_invoice[1]

    cursor.execute("""
        UPDATE invoices
        SET invoice_id = %s
        WHERE invoice_record_id = %s
    """, (
        duplicate_invoice_id,
        second_invoice[0],
    ))

    add_ground_truth(
        ground_truth,
        "ANOM-002",
        "INVOICE",
        str(second_invoice[0]),
        "DUPLICATE_INVOICE",
        f"Invoice number {duplicate_invoice_id} is repeated "
        f"across claims {first_invoice[2]} and {second_invoice[2]}.",
    )


# =====================================================
# 5. PAYMENT OVERSTATEMENT
# =====================================================

def inject_payment_overstatement(cursor, ground_truth):
    """Make one payment exceed its approved claim amount."""

    cursor.execute("""
        SELECT
            p.payment_id,
            p.payment_amount,
            c.approved_amount
        FROM payments p
        JOIN claims c
            ON p.claim_id = c.claim_id
        WHERE p.claim_id = %s
    """, (OVERPAYMENT_CLAIM_ID,))

    result = cursor.fetchone()

    if result is None:
        raise ValueError("Target payment does not exist")

    payment_id, old_amount, approved_amount = result

    new_amount = round(float(approved_amount) + 15000, 2)

    cursor.execute("""
        UPDATE payments
        SET payment_amount = %s,
            payment_status = 'Paid'
        WHERE payment_id = %s
    """, (new_amount, payment_id))

    add_ground_truth(
        ground_truth,
        "ANOM-003",
        "PAYMENT",
        payment_id,
        "PAYMENT_OVERSTATEMENT",
        f"Payment amount {new_amount} exceeds approved amount "
        f"{approved_amount}.",
    )


# =====================================================
# 6. SHARED CONTACT PATTERN
# =====================================================

def inject_shared_contact(cursor, ground_truth):
    """Assign one phone number to five different claimants."""

    claimant_ids = [
        "CTM-2026-000501",
        "CTM-2026-000502",
        "CTM-2026-000503",
        "CTM-2026-000504",
        "CTM-2026-000505",
    ]

    placeholders = ", ".join(["%s"] * len(claimant_ids))

    cursor.execute(
        f"""
        SELECT claimant_id
        FROM claimants
        WHERE claimant_id IN ({placeholders})
        """,
        tuple(claimant_ids),
    )

    found_ids = {row[0] for row in cursor.fetchall()}

    if found_ids != set(claimant_ids):
        raise ValueError("One or more target claimants do not exist")

    cursor.execute(
        f"""
        UPDATE claimants
        SET phone = %s
        WHERE claimant_id IN ({placeholders})
        """,
        (SHARED_PHONE, *claimant_ids),
    )

    for i, claimant_id in enumerate(claimant_ids, start=1):
        add_ground_truth(
            ground_truth,
            f"ANOM-004-{i:02d}",
            "CLAIMANT",
            claimant_id,
            "SHARED_CONTACT_PATTERN",
            f"Claimant shares phone number {SHARED_PHONE} "
            "with four other claimants. This is a suspicious "
            "signal, not proof of fraud.",
        )


# =====================================================
# 7. INCORRECT RELATIONSHIP EDGE
# =====================================================

def inject_incorrect_relationship(cursor, ground_truth):
    """
    Change a claim-provider edge to a nonexistent provider ID.

    The edge count remains unchanged, but the relationship
    becomes invalid and the original provider is recorded.
    """

    cursor.execute("""
        SELECT
            re.edge_id,
            re.target_entity_id,
            i.provider_id
        FROM relationship_edges re
        JOIN invoices i
            ON i.claim_id = re.source_entity_id
        WHERE re.source_entity_type = 'CLAIM'
          AND re.target_entity_type = 'PROVIDER'
          AND re.relationship_type = 'SERVICED_BY'
          AND re.source_entity_id = %s
        LIMIT 1
    """, (INCORRECT_EDGE_CLAIM_ID,))

    result = cursor.fetchone()

    if result is None:
        raise ValueError(
            "Target claim-provider relationship does not exist"
        )

    edge_id, original_provider_id, invoice_provider_id = result

    invalid_provider_id = "PRV-999999"

    cursor.execute("""
        UPDATE relationship_edges
        SET target_entity_id = %s
        WHERE edge_id = %s
    """, (invalid_provider_id, edge_id))

    add_ground_truth(
        ground_truth,
        "ANOM-005",
        "RELATIONSHIP_EDGE",
        edge_id,
        "INVALID_PROVIDER_RELATIONSHIP",
        f"Edge references nonexistent provider {invalid_provider_id}. "
        f"Expected provider: {invoice_provider_id}. "
        f"Original edge target: {original_provider_id}.",
    )


# =====================================================
# 8. SAVE GROUND TRUTH
# =====================================================

def save_ground_truth(records):
    """Save anomaly labels separately from model input data."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        GROUND_TRUTH_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=GROUND_TRUTH_COLUMNS,
        )

        writer.writeheader()
        writer.writerows(records)


# =====================================================
# 9. MAIN ANOMALY GENERATION
# =====================================================

def generate_anomalies():

    if GROUND_TRUTH_FILE.exists():
        raise FileExistsError(
            "ground_truth.csv already exists. "
            "Anomaly generation stopped to prevent duplicate injection."
        )

    connection = get_connection()
    cursor = connection.cursor()

    ground_truth = []

    try:

        print("\nSTARTING CONTROLLED ANOMALY GENERATION")

        print("1. Injecting invalid policy reference...")
        inject_invalid_policy(cursor, ground_truth)

        print("2. Injecting duplicate invoice...")
        inject_duplicate_invoice(cursor, ground_truth)

        print("3. Injecting payment overstatement...")
        inject_payment_overstatement(cursor, ground_truth)

        print("4. Injecting shared contact pattern...")
        inject_shared_contact(cursor, ground_truth)

        print("5. Injecting incorrect relationship edge...")
        inject_incorrect_relationship(cursor, ground_truth)

        connection.commit()

        print("\nANOMALIES INJECTED SUCCESSFULLY")

        print("Ground truth records:", len(ground_truth))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()

    save_ground_truth(ground_truth)

    print("Ground truth saved:", GROUND_TRUTH_FILE)
    print("\nANOMALY GENERATION COMPLETED")


# =====================================================
# 10. EXECUTION
# =====================================================

if __name__ == "__main__":
    generate_anomalies()
