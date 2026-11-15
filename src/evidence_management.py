
import json
from src.storage import get_connection


# --------------------------------------------------
# Generate the next evidence ID
# --------------------------------------------------

def get_next_evidence_number(cursor):
    cursor.execute("""
        SELECT evidence_id
        FROM investigation_evidence
        WHERE evidence_id LIKE 'EVD-2026-%'
    """)

    rows = cursor.fetchall()
    numbers = []

    for row in rows:
        try:
            numbers.append(int(row[0].split("-")[-1]))
        except (ValueError, IndexError):
            continue

    return max(numbers, default=0) + 1


# --------------------------------------------------
# Register new evidence
# --------------------------------------------------

def register_evidence():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        print("\nREGISTER INVESTIGATION EVIDENCE")
        print("=" * 45)

        investigation_id = input(
            "Enter investigation ID: "
        ).strip().upper()

        evidence_type = input(
            "Enter evidence type: "
        ).strip()

        evidence_reference = input(
            "Enter evidence reference: "
        ).strip()

        evidence_description = input(
            "Enter evidence description: "
        ).strip()

        collected_by = input(
            "Enter collector name: "
        ).strip()

        if not all([
            investigation_id,
            evidence_type,
            evidence_reference,
            collected_by
        ]):
            print("Required fields cannot be empty.")
            return

        cursor.execute("""
            SELECT investigation_id
            FROM investigations
            WHERE investigation_id = %s
        """, (investigation_id,))

        if cursor.fetchone() is None:
            print("Investigation ID does not exist.")
            return

        cursor.execute("""
            SELECT evidence_id
            FROM investigation_evidence
            WHERE evidence_reference = %s
        """, (evidence_reference,))

        if cursor.fetchone():
            print("This evidence reference is already registered.")
            return

        next_number = get_next_evidence_number(cursor)
        evidence_id = f"EVD-2026-{next_number:06d}"

        cursor.execute("""
            INSERT INTO investigation_evidence (
                evidence_id,
                investigation_id,
                evidence_type,
                evidence_reference,
                evidence_description,
                collected_by,
                evidence_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            evidence_id,
            investigation_id,
            evidence_type,
            evidence_reference,
            evidence_description,
            collected_by,
            "AVAILABLE"
        ))

        audit_data = {
            "evidence_id": evidence_id,
            "investigation_id": investigation_id,
            "evidence_type": evidence_type,
            "evidence_reference": evidence_reference,
            "evidence_status": "AVAILABLE"
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
            "EVIDENCE",
            evidence_id,
            "EVIDENCE_REGISTERED",
            None,
            json.dumps(audit_data),
            collected_by
        ))

        connection.commit()

        print("\nEVIDENCE REGISTERED SUCCESSFULLY")
        print("Evidence ID:", evidence_id)
        print("Investigation ID:", investigation_id)
        print("Evidence status: AVAILABLE")
        print("Audit record created.")

    except Exception as error:
        connection.rollback()
        print("Evidence registration failed:", error)

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# View all registered evidence
# --------------------------------------------------

def view_evidence():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                evidence_id,
                investigation_id,
                evidence_type,
                evidence_reference,
                evidence_description,
                collected_by,
                collected_at,
                evidence_status
            FROM investigation_evidence
            ORDER BY collected_at DESC
        """)

        rows = cursor.fetchall()

        print("\nINVESTIGATION EVIDENCE REGISTER")
        print("=" * 65)

        if not rows:
            print("No evidence records found.")
            return

        for row in rows:
            print("\nEvidence ID:", row[0])
            print("Investigation ID:", row[1])
            print("Type:", row[2])
            print("Reference:", row[3])
            print("Description:", row[4])
            print("Collected by:", row[5])
            print("Collected at:", row[6])
            print("Status:", row[7])

    except Exception as error:
        print("Unable to retrieve evidence:", error)

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# Update evidence status
# --------------------------------------------------

def update_evidence_status():

    allowed_transitions = {
        "AVAILABLE": {"UNDER_REVIEW", "REJECTED"},
        "UNDER_REVIEW": {"AVAILABLE", "VERIFIED", "REJECTED"},
        "VERIFIED": {"UNDER_REVIEW"},
        "REJECTED": {"UNDER_REVIEW"},
    }

    evidence_id = input(
        "\nEnter evidence ID: "
    ).strip().upper()

    new_status = input(
        "Enter new status (AVAILABLE / UNDER_REVIEW / VERIFIED / REJECTED): "
    ).strip().upper()

    if new_status not in allowed_transitions:
        print("Invalid evidence status.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT evidence_status
            FROM investigation_evidence
            WHERE evidence_id = %s
            FOR UPDATE
        """, (evidence_id,))

        record = cursor.fetchone()

        if record is None:
            print("Evidence ID not found.")
            connection.rollback()
            return

        old_status = record[0]

        if new_status == old_status:
            print("Evidence already has this status.")
            connection.rollback()
            return

        if new_status not in allowed_transitions.get(old_status, set()):
            print(f"Invalid transition: {old_status} -> {new_status}")
            print(
                "Allowed statuses:",
                ", ".join(sorted(allowed_transitions[old_status]))
            )
            connection.rollback()
            return

        cursor.execute("""
            UPDATE investigation_evidence
            SET evidence_status = %s
            WHERE evidence_id = %s
        """, (new_status, evidence_id))

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
            "EVIDENCE",
            evidence_id,
            "EVIDENCE_STATUS_UPDATED",
            json.dumps({"evidence_status": old_status}),
            json.dumps({"evidence_status": new_status}),
            "SYSTEM_USER"
        ))

        connection.commit()

        print("\nEVIDENCE STATUS UPDATED SUCCESSFULLY")
        print("Evidence ID:", evidence_id)
        print("Previous status:", old_status)
        print("New status:", new_status)
        print("Audit record created.")

    except Exception as error:
        connection.rollback()
        print("Evidence status update failed:", error)

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# Main menu
# --------------------------------------------------

def main():

    while True:
        print("\nEVIDENCE MANAGEMENT SYSTEM")
        print("=" * 40)
        print("1. Register evidence")
        print("2. View evidence")
        print("3. Update evidence status")
        print("4. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            register_evidence()

        elif choice == "2":
            view_evidence()

        elif choice == "3":
            update_evidence_status()

        elif choice == "4":
            print("Exiting evidence management system.")
            break

        else:
            print("Invalid choice. Please select 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()
