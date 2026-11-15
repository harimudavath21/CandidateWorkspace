
from src.storage import get_connection


# =====================================================
# 1. DETECTION RULE CONFIGURATION
# =====================================================

RULES = {
    "INVALID_POLICY_REFERENCE": {
        "severity": "HIGH",
        "risk_score": 30.0,
    },
    "DUPLICATE_INVOICE": {
        "severity": "HIGH",
        "risk_score": 25.0,
    },
    "PAYMENT_OVERSTATEMENT": {
        "severity": "CRITICAL",
        "risk_score": 40.0,
    },
    "SHARED_CONTACT_PATTERN": {
        "severity": "MEDIUM",
        "risk_score": 10.0,
    },
    "INVALID_PROVIDER_RELATIONSHIP": {
        "severity": "HIGH",
        "risk_score": 25.0,
    },
}


# =====================================================
# 2. HELPER TO BUILD AN INDICATOR
# =====================================================

def create_indicator(
    indicator_id,
    claim_id,
    indicator_type,
    description,
):
    """Prepare a fraud indicator for database insertion."""

    rule = RULES[indicator_type]

    return (
        indicator_id,
        claim_id,
        indicator_type,
        description,
        rule["severity"],
        rule["risk_score"],
    )


# =====================================================
# 3. DETECT INVALID POLICY REFERENCES
# =====================================================

def detect_invalid_policy(cursor):
    """Find claims with invalid policy references."""

    cursor.execute("""
        SELECT
            dqi.entity_id,
            dqi.invalid_value,
            dqi.issue_description
        FROM data_quality_issues dqi
        JOIN claims c
            ON c.claim_id = dqi.entity_id
        WHERE dqi.entity_type = 'CLAIM'
          AND dqi.issue_type = 'INVALID_POLICY_REFERENCE'
    """)

    results = cursor.fetchall()
    indicators = []

    for claim_id, invalid_policy, description in results:

        indicators.append(
            create_indicator(
                f"DET-POL-{claim_id}",
                claim_id,
                "INVALID_POLICY_REFERENCE",
                (
                    f"Claim references nonexistent policy "
                    f"{invalid_policy}. {description}"
                ),
            )
        )

    return indicators


# =====================================================
# 4. DETECT DUPLICATE INVOICES
# =====================================================

def detect_duplicate_invoices(cursor):
    """Identify duplicate invoice numbers across claims."""

    cursor.execute("""
        SELECT
            i.invoice_record_id,
            i.invoice_id,
            i.claim_id,
            i.invoice_amount
        FROM invoices i
        INNER JOIN (
            SELECT invoice_id
            FROM invoices
            GROUP BY invoice_id
            HAVING COUNT(*) > 1
        ) duplicates
            ON i.invoice_id = duplicates.invoice_id
        ORDER BY i.invoice_record_id
    """)

    results = cursor.fetchall()
    indicators = []

    for record_id, invoice_id, claim_id, amount in results:

        indicators.append(
            create_indicator(
                f"DET-INV-{record_id:010d}",
                claim_id,
                "DUPLICATE_INVOICE",
                (
                    f"Invoice number {invoice_id} is duplicated. "
                    f"Invoice record: {record_id}. "
                    f"Invoice amount: {amount}."
                ),
            )
        )

    return indicators


# =====================================================
# 5. DETECT PAYMENT OVERSTATEMENT
# =====================================================

def detect_payment_overstatement(cursor):
    """Find payments exceeding approved claim amounts."""

    cursor.execute("""
        SELECT
            p.payment_id,
            p.claim_id,
            p.payment_amount,
            c.approved_amount
        FROM payments p
        INNER JOIN claims c
            ON p.claim_id = c.claim_id
        WHERE p.payment_amount > c.approved_amount
          AND p.payment_amount > 0
    """)

    results = cursor.fetchall()
    indicators = []

    for payment_id, claim_id, payment_amount, approved_amount in results:

        difference = float(payment_amount) - float(approved_amount)

        indicators.append(
            create_indicator(
                f"DET-PAY-{payment_id}",
                claim_id,
                "PAYMENT_OVERSTATEMENT",
                (
                    f"Payment {payment_id} exceeds the approved "
                    f"claim amount by {difference:.2f}. "
                    f"Paid: {payment_amount}; "
                    f"approved: {approved_amount}."
                ),
            )
        )

    return indicators


# =====================================================
# 6. DETECT SHARED CONTACT PATTERNS
# =====================================================

def detect_shared_contacts(cursor):
    """
    Identify claimants sharing phone numbers.

    A shared contact is a risk signal, not proof of fraud.
    One representative claim is selected per claimant.
    """

    cursor.execute("""
        SELECT
            c.claimant_id,
            c.phone,
            MIN(cl.claim_id) AS representative_claim,
            COUNT(DISTINCT other.claimant_id) AS shared_count
        FROM claimants c
        INNER JOIN claims cl
            ON cl.claimant_id = c.claimant_id
        INNER JOIN claimants other
            ON other.phone = c.phone
           AND other.claimant_id <> c.claimant_id
        WHERE c.phone IS NOT NULL
          AND TRIM(c.phone) <> ''
        GROUP BY c.claimant_id, c.phone
        ORDER BY c.claimant_id
    """)

    results = cursor.fetchall()
    indicators = []

    for claimant_id, phone, claim_id, shared_count in results:

        indicators.append(
            create_indicator(
                f"DET-SHR-{claimant_id}",
                claim_id,
                "SHARED_CONTACT_PATTERN",
                (
                    f"Claimant {claimant_id} shares phone number "
                    f"{phone} with {shared_count} other claimant(s). "
                    "This is a suspicious signal requiring review, "
                    "not proof of fraud."
                ),
            )
        )

    return indicators


# =====================================================
# 7. DETECT INVALID PROVIDER RELATIONSHIPS
# =====================================================

def detect_invalid_provider_relationships(cursor):
    """Find claim-provider edges pointing to nonexistent providers."""

    cursor.execute("""
        SELECT
            re.edge_id,
            re.source_entity_id,
            re.target_entity_id
        FROM relationship_edges re
        LEFT JOIN providers p
            ON p.provider_id = re.target_entity_id
        WHERE re.source_entity_type = 'CLAIM'
          AND re.target_entity_type = 'PROVIDER'
          AND p.provider_id IS NULL
    """)

    results = cursor.fetchall()
    indicators = []

    for edge_id, claim_id, provider_id in results:

        indicators.append(
            create_indicator(
                f"DET-EDG-{edge_id}",
                claim_id,
                "INVALID_PROVIDER_RELATIONSHIP",
                (
                    f"Relationship edge {edge_id} references "
                    f"nonexistent provider {provider_id}."
                ),
            )
        )

    return indicators


# =====================================================
# 8. SAVE INDICATORS TO MYSQL
# =====================================================

def save_indicators(cursor, indicators):
    """Insert or update detection results without duplicates."""

    if not indicators:
        return

    cursor.executemany(
        """
        INSERT INTO fraud_indicators (
            indicator_id,
            claim_id,
            indicator_type,
            indicator_description,
            severity,
            risk_score
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            claim_id = VALUES(claim_id),
            indicator_type = VALUES(indicator_type),
            indicator_description = VALUES(indicator_description),
            severity = VALUES(severity),
            risk_score = VALUES(risk_score)
        """,
        indicators,
    )


# =====================================================
# 9. RUN COMPLETE DETECTION ENGINE
# =====================================================

def run_detection():
    """Execute all fraud detection rules and save findings."""

    connection = get_connection()
    cursor = connection.cursor()

    all_indicators = []

    try:

        print("\nINSURANCE FRAUD DETECTION ENGINE")
        print("=" * 45)

        detection_functions = [
            detect_invalid_policy,
            detect_duplicate_invoices,
            detect_payment_overstatement,
            detect_shared_contacts,
            detect_invalid_provider_relationships,
        ]

        for detection_function in detection_functions:

            indicators = detection_function(cursor)

            all_indicators.extend(indicators)

            print(
                f"{detection_function.__name__}: "
                f"{len(indicators)} findings"
            )

        save_indicators(cursor, all_indicators)

        connection.commit()

        print("\nDETECTION COMPLETED SUCCESSFULLY")
        print("Total indicators:", len(all_indicators))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 10. VIEW DETECTION SUMMARY
# =====================================================

def show_detection_summary():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                indicator_type,
                severity,
                COUNT(*) AS total_indicators,
                ROUND(AVG(risk_score), 2) AS average_risk_score
            FROM fraud_indicators
            GROUP BY indicator_type, severity
            ORDER BY average_risk_score DESC
        """)

        results = cursor.fetchall()

        print("\nFRAUD DETECTION SUMMARY")
        print("=" * 65)

        for row in results:
            print(
                f"Type: {row[0]} | "
                f"Severity: {row[1]} | "
                f"Count: {row[2]} | "
                f"Average risk: {row[3]}"
            )

        print("=" * 65)

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 11. MAIN EXECUTION
# =====================================================

if __name__ == "__main__":

    run_detection()
    show_detection_summary()
