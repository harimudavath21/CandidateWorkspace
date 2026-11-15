
from src.storage import get_connection


# --------------------------------------------------
# Expected dataset sizes
# --------------------------------------------------

EXPECTED_COUNTS = {
    "claimants": 2000,
    "policies": 2000,
    "incidents": 5000,
    "providers": 500,
    "claims": 5000,
    "invoices": 5000,
    "payments": 5000,
    "relationship_edges": 8000,
}


# --------------------------------------------------
# Helper function
# --------------------------------------------------

def get_count(cursor, query):
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0] if result else 0


def print_result(name, count, expected=None):
    if expected is None:
        print(f"[INFO] {name}: {count}")
    elif count == expected:
        print(f"[PASS] {name}: {count}")
    else:
        print(
            f"[WARNING] {name}: Found {count}, "
            f"Expected {expected}"
        )


# --------------------------------------------------
# 1. Validate dataset record counts
# --------------------------------------------------

def validate_record_counts(cursor):
    print("\n1. DATASET RECORD COUNT VALIDATION")
    print("-" * 55)

    for table, expected in EXPECTED_COUNTS.items():
        count = get_count(
            cursor,
            f"SELECT COUNT(*) FROM {table}"
        )

        print_result(table, count, expected)


# --------------------------------------------------
# 2. Validate claim references
# --------------------------------------------------

def validate_claim_references(cursor):
    print("\n2. CLAIM REFERENCE VALIDATION")
    print("-" * 55)

    checks = {
        "Claims with missing claimant": """
            SELECT COUNT(*)
            FROM claims c
            LEFT JOIN claimants ct
                ON c.claimant_id = ct.claimant_id
            WHERE ct.claimant_id IS NULL
        """,

        "Claims with missing policy": """
            SELECT COUNT(*)
            FROM claims c
            LEFT JOIN policies p
                ON c.policy_id = p.policy_id
            WHERE c.policy_id IS NOT NULL
              AND p.policy_id IS NULL
        """,

        "Claims with NULL policy reference": """
            SELECT COUNT(*)
            FROM claims
            WHERE policy_id IS NULL
        """,

        "Claims with missing incident": """
            SELECT COUNT(*)
            FROM claims c
            LEFT JOIN incidents i
                ON c.incident_id = i.incident_id
            WHERE i.incident_id IS NULL
        """
    }

    for name, query in checks.items():
        count = get_count(cursor, query)

        if count > 0:
            print(f"[WARNING] {name}: {count}")
        else:
            print(f"[PASS] {name}: 0")


# --------------------------------------------------
# 3. Detect duplicate invoice numbers
# --------------------------------------------------

def validate_duplicate_invoices(cursor):
    print("\n3. DUPLICATE INVOICE VALIDATION")
    print("-" * 55)

    query = """
        SELECT COUNT(*)
        FROM (
            SELECT invoice_id
            FROM invoices
            GROUP BY invoice_id
            HAVING COUNT(*) > 1
        ) duplicate_invoices
    """

    count = get_count(cursor, query)

    if count > 0:
        print(
            f"[WARNING] Duplicate invoice groups detected: {count}"
        )
    else:
        print("[PASS] No duplicate invoice numbers found.")


# --------------------------------------------------
# 4. Detect payment overstatement
# --------------------------------------------------

def validate_payment_amounts(cursor):
    print("\n4. PAYMENT AMOUNT VALIDATION")
    print("-" * 55)

    query = """
        SELECT COUNT(*)
        FROM payments p
        JOIN claims c
            ON p.claim_id = c.claim_id
        WHERE p.payment_amount > COALESCE(c.approved_amount, 0)
    """

    count = get_count(cursor, query)

    if count > 0:
        print(
            f"[WARNING] Payments exceeding approved amounts: {count}"
        )
    else:
        print("[PASS] No payment overstatements found.")


# --------------------------------------------------
# 5. Detect shared claimant phone numbers
# --------------------------------------------------

def validate_shared_contacts(cursor):
    print("\n5. SHARED CONTACT VALIDATION")
    print("-" * 55)

    query = """
        SELECT COUNT(*)
        FROM (
            SELECT phone
            FROM claimants
            WHERE phone IS NOT NULL
              AND phone <> ''
            GROUP BY phone
            HAVING COUNT(*) > 1
        ) shared_contacts
    """

    count = get_count(cursor, query)

    if count > 0:
        print(
            f"[WARNING] Shared phone number groups detected: {count}"
        )
    else:
        print("[PASS] No shared phone number groups found.")


# --------------------------------------------------
# 6. Validate provider relationship references
# --------------------------------------------------

def validate_provider_relationships(cursor):
    print("\n6. PROVIDER RELATIONSHIP VALIDATION")
    print("-" * 55)

    query = """
        SELECT COUNT(*)
        FROM relationship_edges re
        LEFT JOIN providers p
            ON re.target_entity_id = p.provider_id
        WHERE re.target_entity_type = 'PROVIDER'
          AND p.provider_id IS NULL
    """

    count = get_count(cursor, query)

    if count > 0:
        print(
            f"[WARNING] Invalid provider relationships: {count}"
        )
    else:
        print("[PASS] All provider relationships are valid.")


# --------------------------------------------------
# 7. Validate data quality issue records
# --------------------------------------------------

def validate_quality_issue_records(cursor):
    print("\n7. DATA QUALITY ISSUE REGISTER")
    print("-" * 55)

    query = """
        SELECT COUNT(*)
        FROM data_quality_issues
    """

    count = get_count(cursor, query)

    print_result("Recorded data quality issues", count)


# --------------------------------------------------
# 8. Run complete validation
# --------------------------------------------------

def run_validation():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        print("\nINSURANCE FRAUD DATA QUALITY VALIDATION")
        print("=" * 65)

        validate_record_counts(cursor)
        validate_claim_references(cursor)
        validate_duplicate_invoices(cursor)
        validate_payment_amounts(cursor)
        validate_shared_contacts(cursor)
        validate_provider_relationships(cursor)
        validate_quality_issue_records(cursor)

        print("\n" + "=" * 65)
        print("DATA QUALITY VALIDATION COMPLETED")
        print("=" * 65)

    except Exception as error:
        print("\nDATA QUALITY VALIDATION FAILED")
        print("Error:", error)

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


# --------------------------------------------------
# Main entry point
# --------------------------------------------------

if __name__ == "__main__":
    run_validation()
