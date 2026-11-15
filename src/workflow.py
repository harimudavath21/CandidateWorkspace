
import json

from src.storage import get_connection


# =====================================================
# 1. INVESTIGATION CONFIGURATION
# =====================================================

INVESTIGATORS = [
    "Investigator-01",
    "Investigator-02",
    "Investigator-03",
    "Investigator-04",
    "Investigator-05",
]


# =====================================================
# 2. DETERMINE INVESTIGATION PRIORITY
# =====================================================

def determine_priority(risk_score):

    if risk_score >= 70:
        return "CRITICAL"

    elif risk_score >= 40:
        return "HIGH"

    elif risk_score >= 20:
        return "MEDIUM"

    return "LOW"


# =====================================================
# 3. GENERATE NEXT INVESTIGATION ID
# =====================================================

def get_next_investigation_number(cursor):

    cursor.execute("""
        SELECT investigation_id
        FROM investigations
        WHERE investigation_id LIKE 'INVG-2026-%'
    """)

    existing_ids = cursor.fetchall()

    numbers = []

    for row in existing_ids:
        try:
            numbers.append(int(row[0].split("-")[-1]))
        except (ValueError, IndexError):
            continue

    return max(numbers, default=0) + 1


# =====================================================
# 4. GENERATE NEXT EVENT ID
# =====================================================

def get_next_event_number(cursor):

    cursor.execute("""
        SELECT event_id
        FROM investigation_events
        WHERE event_id LIKE 'EVT-2026-%'
    """)

    existing_ids = cursor.fetchall()

    numbers = []

    for row in existing_ids:
        try:
            numbers.append(int(row[0].split("-")[-1]))
        except (ValueError, IndexError):
            continue

    return max(numbers, default=0) + 1


# =====================================================
# 5. CREATE INVESTIGATIONS
# =====================================================

def create_investigations():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        print("\nINVESTIGATION MANAGEMENT SYSTEM")
        print("=" * 55)

        # Get suspicious claims
        cursor.execute("""
            SELECT
                claim_id,
                total_risk_score,
                risk_category,
                indicator_count,
                risk_explanation
            FROM claim_risk_scores
            WHERE indicator_count > 0
            ORDER BY total_risk_score DESC, claim_id
        """)

        suspicious_claims = cursor.fetchall()

        if not suspicious_claims:
            print("No suspicious claims available.")
            return

        # Existing investigations
        cursor.execute("""
            SELECT claim_id
            FROM investigations
        """)

        existing_claims = {
            row[0] for row in cursor.fetchall()
        }

        next_investigation = get_next_investigation_number(
            cursor
        )

        next_event = get_next_event_number(cursor)

        created_count = 0

        for claim_id, risk_score, category, count, explanation in suspicious_claims:

            if claim_id in existing_claims:
                continue

            investigation_id = (
                f"INVG-2026-{next_investigation:06d}"
            )

            investigator = INVESTIGATORS[
                created_count % len(INVESTIGATORS)
            ]

            priority = determine_priority(
                float(risk_score)
            )

            notes = (
                f"Automatically created for review. "
                f"Detected indicators: {count}. "
                f"Risk explanation: {explanation}"
            )

            # -------------------------------------
            # Insert investigation
            # -------------------------------------

            cursor.execute("""
                INSERT INTO investigations (
                    investigation_id,
                    claim_id,
                    assigned_investigator,
                    investigation_status,
                    priority,
                    risk_score,
                    investigation_notes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                investigation_id,
                claim_id,
                investigator,
                "OPEN",
                priority,
                risk_score,
                notes,
            ))

            # -------------------------------------
            # Record investigation event
            # -------------------------------------

            event_id = f"EVT-2026-{next_event:06d}"

            cursor.execute("""
                INSERT INTO investigation_events (
                    event_id,
                    investigation_id,
                    event_type,
                    event_description,
                    performed_by
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                event_id,
                investigation_id,
                "INVESTIGATION_OPENED",
                (
                    f"Investigation opened for claim {claim_id}. "
                    f"Risk score: {risk_score}. "
                    f"Priority: {priority}."
                ),
                "SYSTEM",
            ))

            # -------------------------------------
            # Record audit log
            # -------------------------------------

            new_value = {
                "investigation_id": investigation_id,
                "claim_id": claim_id,
                "assigned_investigator": investigator,
                "status": "OPEN",
                "priority": priority,
                "risk_score": float(risk_score),
            }

            cursor.execute("""
                INSERT INTO audit_logs (
                    entity_type,
                    entity_id,
                    action,
                    old_value,
                    new_value,
                    performed_by
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "INVESTIGATION",
                investigation_id,
                "INVESTIGATION_CREATED",
                None,
                json.dumps(new_value),
                "SYSTEM",
            ))

            print(
                f"Created: {investigation_id} | "
                f"Claim: {claim_id} | "
                f"Priority: {priority}"
            )

            next_investigation += 1
            next_event += 1
            created_count += 1

        connection.commit()

        print("\nINVESTIGATION CREATION COMPLETED")
        print("New investigations:", created_count)
        print("Already existing:", len(existing_claims))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 6. DISPLAY INVESTIGATION SUMMARY
# =====================================================

def show_investigation_summary():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                investigation_status,
                priority,
                COUNT(*) AS total
            FROM investigations
            GROUP BY investigation_status, priority
            ORDER BY investigation_status, priority
        """)

        results = cursor.fetchall()

        print("\nINVESTIGATION SUMMARY")
        print("=" * 55)

        for status, priority, total in results:

            print(
                f"Status: {status} | "
                f"Priority: {priority} | "
                f"Count: {total}"
            )

        cursor.execute("""
            SELECT COUNT(*)
            FROM investigation_events
        """)

        event_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM audit_logs
        """)

        audit_count = cursor.fetchone()[0]

        print("\nTotal investigation events:", event_count)
        print("Total audit records:", audit_count)

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 7. MAIN EXECUTION
# =====================================================

if __name__ == "__main__":

    create_investigations()
    show_investigation_summary()
