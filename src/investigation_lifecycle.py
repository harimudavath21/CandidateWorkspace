
import json
from src.storage import get_connection


ALLOWED_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "ON_HOLD", "CLOSED"},
    "IN_PROGRESS": {"OPEN", "ON_HOLD", "CLOSED"},
    "ON_HOLD": {"IN_PROGRESS", "CLOSED"},
    "CLOSED": {"OPEN"},
}


def get_next_event_number(cursor):
    cursor.execute("""
        SELECT event_id
        FROM investigation_events
        WHERE event_id LIKE 'EVT-2026-%'
    """)
    rows = cursor.fetchall()

    numbers = []
    for row in rows:
        try:
            numbers.append(int(row[0].split("-")[-1]))
        except (ValueError, IndexError):
            continue

    return max(numbers, default=0) + 1


def show_investigations():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT investigation_id, claim_id,
                   assigned_investigator, investigation_status,
                   priority, risk_score
            FROM investigations
            ORDER BY investigation_id
        """)

        rows = cursor.fetchall()

        print("\nINVESTIGATION REGISTER")
        print("=" * 90)

        if not rows:
            print("No investigations found.")
            return

        for row in rows:
            investigation_id, claim_id, investigator, status, priority, score = row

            print(
                f"{investigation_id} | Claim: {claim_id} | "
                f"Investigator: {investigator} | "
                f"Status: {status} | Priority: {priority} | "
                f"Risk: {float(score):.2f}"
            )

        print("=" * 90)

    finally:
        cursor.close()
        connection.close()


def update_investigation_status():
    investigation_id = input(
        "\nEnter investigation ID: "
    ).strip().upper()

    new_status = input(
        "Enter new status (OPEN / IN_PROGRESS / ON_HOLD / CLOSED): "
    ).strip().upper()

    if new_status not in ALLOWED_TRANSITIONS:
        print("Invalid status.")
        return

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT investigation_id, claim_id,
                   assigned_investigator, investigation_status,
                   priority, risk_score
            FROM investigations
            WHERE investigation_id = %s
            FOR UPDATE
        """, (investigation_id,))

        investigation = cursor.fetchone()

        if not investigation:
            print("Investigation ID not found.")
            connection.rollback()
            return

        (
            current_id,
            claim_id,
            investigator,
            old_status,
            priority,
            risk_score
        ) = investigation

        if new_status == old_status:
            print("Investigation already has this status.")
            connection.rollback()
            return

        if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
            allowed = ALLOWED_TRANSITIONS.get(old_status, set())
            print(f"Invalid transition: {old_status} -> {new_status}")
            print("Allowed next statuses:", ", ".join(sorted(allowed)))
            connection.rollback()
            return

        cursor.execute("""
            UPDATE investigations
            SET investigation_status = %s,
                closed_at = CASE
                    WHEN %s = 'CLOSED' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE investigation_id = %s
        """, (new_status, new_status, investigation_id))

        event_number = get_next_event_number(cursor)
        event_id = f"EVT-2026-{event_number:06d}"

        event_description = (
            f"Investigation status changed from "
            f"{old_status} to {new_status} for claim {claim_id}."
        )

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
            "STATUS_CHANGED",
            event_description,
            "SYSTEM_USER"
        ))

        old_value = {
            "investigation_status": old_status
        }

        new_value = {
            "investigation_status": new_status
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
            "INVESTIGATION_STATUS_UPDATED",
            json.dumps(old_value),
            json.dumps(new_value),
            "SYSTEM_USER"
        ))

        connection.commit()

        print("\nSTATUS UPDATED SUCCESSFULLY")
        print("Investigation:", investigation_id)
        print("Claim:", claim_id)
        print("Previous status:", old_status)
        print("New status:", new_status)
        print("Event recorded:", event_id)
        print("Audit record created successfully.")

    except Exception as error:
        connection.rollback()
        print("Error updating investigation:", error)

    finally:
        cursor.close()
        connection.close()


def main():
    while True:
        print("\nINVESTIGATION LIFECYCLE MANAGEMENT")
        print("=" * 45)
        print("1. View investigations")
        print("2. Update investigation status")
        print("3. Exit")

        choice = input("Choose an option: ").strip()

        if choice == "1":
            show_investigations()

        elif choice == "2":
            update_investigation_status()

        elif choice == "3":
            print("Exiting investigation lifecycle management.")
            break

        else:
            print("Invalid choice. Select 1, 2, or 3.")


if __name__ == "__main__":
    main()
