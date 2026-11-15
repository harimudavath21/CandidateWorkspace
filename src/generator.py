
import random
from datetime import date, timedelta

from faker import Faker

from config import (
    TOTAL_CLAIMANTS,
    TOTAL_POLICIES,
    TOTAL_PROVIDERS,
    TOTAL_INCIDENTS,
    TOTAL_CLAIMS,
    RANDOM_SEED,
)

from src.storage import get_connection


# =====================================================
# 1. REPRODUCIBILITY CONFIGURATION
# =====================================================

fake = Faker("en_IN")

Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


# =====================================================
# 2. DATABASE COUNT HELPER
# =====================================================

def get_table_count(cursor, table_name):
    """Return the number of records in a project table."""

    allowed_tables = {
        "claimants",
        "providers",
        "policies",
        "incidents",
        "claims",
        "invoices",
        "payments",
        "relationship_edges",
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name")

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")

    return cursor.fetchone()[0]


# =====================================================
# 3. GENERATE CLAIMANTS
# =====================================================

def generate_claimants():
    """Generate synthetic claimant records."""

    rows = []

    for i in range(1, TOTAL_CLAIMANTS + 1):

        claimant_id = f"CTM-2026-{i:06d}"

        rows.append((
            claimant_id,
            fake.name(),
            random.randint(18, 85),
            random.choice(["Male", "Female", "Other"]),
            fake.street_address()[:255],
            fake.city(),
            fake.phone_number()[:20],
            f"claimant{i}@example.com",
        ))

    return rows


# =====================================================
# 4. GENERATE PROVIDERS
# =====================================================

def generate_providers():
    """Generate synthetic insurance service providers."""

    rows = []

    provider_types = [
        "Hospital",
        "Vehicle Repair",
        "Diagnostic Center",
        "Pharmacy",
        "Legal Service",
    ]

    for i in range(1, TOTAL_PROVIDERS + 1):

        provider_id = f"PRV-{i:06d}"

        rows.append((
            provider_id,
            fake.company()[:150],
            random.choice(provider_types),
            fake.address()[:255],
            fake.phone_number()[:20],
            fake.date_between(
                start_date="-10y",
                end_date="today"
            ),
        ))

    return rows


# =====================================================
# 5. GENERATE POLICIES
# =====================================================

def generate_policies():
    """Generate policies linked to claimants."""

    rows = []

    today = date.today()

    policy_types = [
        "Health",
        "Vehicle",
        "Property",
        "Life",
        "Travel",
    ]

    for i in range(1, TOTAL_POLICIES + 1):

        policy_id = f"POL-2026-{i:06d}"
        claimant_id = f"CTM-2026-{i:06d}"

        start_date = fake.date_between(
            start_date="-4y",
            end_date="today"
        )

        end_date = start_date + timedelta(days=365 * 2)

        status = (
            "Active" if end_date >= today else "Expired"
        )

        premium = round(
            random.uniform(5000, 50000), 2
        )

        coverage = round(
            random.uniform(100000, 2000000), 2
        )

        rows.append((
            policy_id,
            claimant_id,
            random.choice(policy_types),
            start_date,
            end_date,
            premium,
            coverage,
            status,
        ))

    return rows


# =====================================================
# 6. GENERATE INCIDENTS
# =====================================================

def generate_incidents():
    """Generate synthetic insurance incidents."""

    rows = []

    incident_types = [
        "Vehicle Accident",
        "Medical Emergency",
        "Property Damage",
        "Fire Damage",
        "Theft",
    ]

    for i in range(1, TOTAL_INCIDENTS + 1):

        incident_id = f"INC-2026-{i:06d}"

        rows.append((
            incident_id,
            random.choice(incident_types),
            fake.date_between(
                start_date="-2y",
                end_date="today"
            ),
            fake.address()[:255],
            fake.text(max_nb_chars=200),
            round(random.uniform(10000, 500000), 2),
        ))

    return rows


# =====================================================
# 7. INSERT HELPER
# =====================================================

def insert_records(cursor, sql, rows):
    """Insert multiple records into MySQL."""

    cursor.executemany(sql, rows)


# =====================================================
# 8. GENERATE AND INSERT BASE DATA
# =====================================================

def generate_base_data():
    """Generate claimants, providers, policies and incidents."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        base_tables = [
            "claimants",
            "providers",
            "policies",
            "incidents",
        ]

        for table in base_tables:

            if get_table_count(cursor, table) > 0:
                raise ValueError(
                    f"{table} already contains records. "
                    "Generation stopped to prevent duplicates."
                )

        print("Generating claimants...")

        claimants = generate_claimants()

        insert_records(
            cursor,
            """
            INSERT INTO claimants (
                claimant_id, full_name, age, gender,
                address, city, phone, email
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            claimants,
        )

        print("Generating providers...")

        providers = generate_providers()

        insert_records(
            cursor,
            """
            INSERT INTO providers (
                provider_id, provider_name, provider_type,
                address, phone, registration_date
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            providers,
        )

        print("Generating policies...")

        policies = generate_policies()

        insert_records(
            cursor,
            """
            INSERT INTO policies (
                policy_id, claimant_id, policy_type,
                start_date, end_date, premium_amount,
                coverage_amount, policy_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            policies,
        )

        print("Generating incidents...")

        incidents = generate_incidents()

        insert_records(
            cursor,
            """
            INSERT INTO incidents (
                incident_id, incident_type, incident_date,
                incident_location, description, estimated_damage
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            incidents,
        )

        connection.commit()

        print("\nBASE DATA GENERATED SUCCESSFULLY")
        print("Claimants:", len(claimants))
        print("Providers:", len(providers))
        print("Policies:", len(policies))
        print("Incidents:", len(incidents))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 9. GENERATE CLAIMS
# =====================================================

def generate_claims():
    """Generate claims linked to claimants, policies and incidents."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        if get_table_count(cursor, "claims") > 0:
            raise ValueError(
                "Claims already exist. Generation stopped."
            )

        cursor.execute("""
            SELECT policy_id, claimant_id
            FROM policies
            ORDER BY policy_id
        """)

        policies = cursor.fetchall()

        cursor.execute("""
            SELECT incident_id, incident_date, incident_type
            FROM incidents
            ORDER BY incident_id
        """)

        incidents = cursor.fetchall()

        if len(policies) != TOTAL_POLICIES:
            raise ValueError("Unexpected policy count")

        if len(incidents) != TOTAL_INCIDENTS:
            raise ValueError("Unexpected incident count")

        rows = []

        statuses = [
            "Submitted",
            "Under Review",
            "Approved",
            "Rejected",
            "Paid",
        ]

        for i in range(1, TOTAL_CLAIMS + 1):

            policy_id, claimant_id = policies[
                (i - 1) % len(policies)
            ]

            incident_id, incident_date, incident_type = incidents[
                (i - 1) % len(incidents)
            ]

            claim_date = incident_date + timedelta(
                days=random.randint(1, 30)
            )

            claimed_amount = round(
                random.uniform(10000, 300000), 2
            )

            approved_amount = round(
                claimed_amount * random.uniform(0.65, 1.0), 2
            )

            claim_id = f"CLM-2026-{i:06d}"

            rows.append((
                claim_id,
                claimant_id,
                policy_id,
                incident_id,
                claim_date,
                claimed_amount,
                approved_amount,
                random.choice(statuses),
                f"Insurance claim for {incident_type}",
            ))

        cursor.executemany(
            """
            INSERT INTO claims (
                claim_id, claimant_id, policy_id,
                incident_id, claim_date,
                claimed_amount, approved_amount,
                claim_status, description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )

        connection.commit()

        print("\nCLAIMS GENERATED SUCCESSFULLY")
        print("Total claims:", len(rows))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 10. GENERATE INVOICES
# =====================================================

def generate_invoices():
    """Generate invoices linked to claims and providers."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        if get_table_count(cursor, "invoices") > 0:
            raise ValueError(
                "Invoices already exist. Generation stopped."
            )

        cursor.execute("""
            SELECT claim_id, claimed_amount
            FROM claims
            ORDER BY claim_id
        """)

        claims_data = cursor.fetchall()

        cursor.execute("""
            SELECT provider_id
            FROM providers
            ORDER BY provider_id
        """)

        providers = cursor.fetchall()

        if len(claims_data) != TOTAL_CLAIMS:
            raise ValueError("Unexpected claims count")

        if len(providers) != TOTAL_PROVIDERS:
            raise ValueError("Unexpected providers count")

        rows = []

        for i, (claim_id, claimed_amount) in enumerate(
            claims_data, start=1
        ):

            provider_id = providers[
                (i - 1) % len(providers)
            ][0]

            invoice_id = (
                f"INV-PRV-{provider_id}-{i:06d}"
            )

            invoice_amount = round(
                float(claimed_amount) * random.uniform(0.70, 1.0),
                2
            )

            rows.append((
                invoice_id,
                claim_id,
                provider_id,
                fake.date_between(
                    start_date="-2y",
                    end_date="today"
                ),
                invoice_amount,
                "Synthetic insurance service invoice",
            ))

        cursor.executemany(
            """
            INSERT INTO invoices (
                invoice_id, claim_id, provider_id,
                invoice_date, invoice_amount, description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows,
        )

        connection.commit()

        print("\nINVOICES GENERATED SUCCESSFULLY")
        print("Total invoices:", len(rows))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 11. GENERATE PAYMENTS
# =====================================================

def generate_payments():
    """Generate payment records linked to claims."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        if get_table_count(cursor, "payments") > 0:
            raise ValueError(
                "Payments already exist. Generation stopped."
            )

        cursor.execute("""
            SELECT claim_id, approved_amount, claim_date,
                   claim_status
            FROM claims
            ORDER BY claim_id
        """)

        claims_data = cursor.fetchall()

        if len(claims_data) != TOTAL_CLAIMS:
            raise ValueError("Unexpected claims count")

        rows = []

        payment_methods = [
            "UPI",
            "Bank Transfer",
            "NEFT",
            "Cheque",
        ]

        for i, (
            claim_id,
            approved_amount,
            claim_date,
            claim_status
        ) in enumerate(claims_data, start=1):

            if claim_status == "Paid":

                payment_status = "Paid"

                payment_amount = round(
                    float(approved_amount) *
                    random.uniform(0.95, 1.0),
                    2
                )

            elif claim_status == "Rejected":

                payment_status = "Failed"
                payment_amount = 0.00

            else:

                payment_status = "Pending"
                payment_amount = 0.00

            payment_date = claim_date + timedelta(
                days=random.randint(1, 30)
            )

            payment_id = f"PAY-2026-{i:06d}"

            rows.append((
                payment_id,
                claim_id,
                payment_date,
                payment_amount,
                payment_status,
                random.choice(payment_methods),
            ))

        cursor.executemany(
            """
            INSERT INTO payments (
                payment_id, claim_id, payment_date,
                payment_amount, payment_status,
                payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            rows,
        )

        connection.commit()

        print("\nPAYMENTS GENERATED SUCCESSFULLY")
        print("Total payments:", len(rows))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 12. GENERATE RELATIONSHIP EDGES
# =====================================================

def generate_relationship_edges():
    """Generate exactly 8,000 insurance relationship edges."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        if get_table_count(cursor, "relationship_edges") > 0:
            raise ValueError(
                "Relationship edges already exist. "
                "Generation stopped."
            )

        rows = []

        # ---------------------------------------------
        # A. CLAIMANT -> POLICY (2,000)
        # ---------------------------------------------

        cursor.execute("""
            SELECT claimant_id, policy_id
            FROM policies
            ORDER BY policy_id
        """)

        policy_links = cursor.fetchall()

        for i, (claimant_id, policy_id) in enumerate(
            policy_links, start=1
        ):

            rows.append((
                f"EDGE-{i:06d}",
                "CLAIMANT",
                claimant_id,
                "POLICY",
                policy_id,
                "OWNS_POLICY",
                1.00,
            ))

        # ---------------------------------------------
        # B. CLAIM -> INCIDENT (3,000)
        # ---------------------------------------------

        cursor.execute("""
            SELECT claim_id, incident_id
            FROM claims
            ORDER BY claim_id
            LIMIT 3000
        """)

        claim_incident_links = cursor.fetchall()

        for i, (claim_id, incident_id) in enumerate(
            claim_incident_links, start=2001
        ):

            rows.append((
                f"EDGE-{i:06d}",
                "CLAIM",
                claim_id,
                "INCIDENT",
                incident_id,
                "REPORTS_INCIDENT",
                1.00,
            ))

        # ---------------------------------------------
        # C. CLAIM -> PROVIDER (3,000)
        # ---------------------------------------------

        cursor.execute("""
            SELECT claim_id, provider_id
            FROM invoices
            ORDER BY claim_id
            LIMIT 3000
        """)

        claim_provider_links = cursor.fetchall()

        for i, (claim_id, provider_id) in enumerate(
            claim_provider_links, start=5001
        ):

            rows.append((
                f"EDGE-{i:06d}",
                "CLAIM",
                claim_id,
                "PROVIDER",
                provider_id,
                "SERVICED_BY",
                1.00,
            ))

        if len(rows) != 8000:
            raise ValueError(
                f"Expected 8000 edges, generated {len(rows)}"
            )

        cursor.executemany(
            """
            INSERT INTO relationship_edges (
                edge_id,
                source_entity_type,
                source_entity_id,
                target_entity_type,
                target_entity_id,
                relationship_type,
                weight
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )

        connection.commit()

        print("\nRELATIONSHIP EDGES GENERATED SUCCESSFULLY")

        print("Claimant-Policy:", len(policy_links))
        print("Claim-Incident:", len(claim_incident_links))
        print("Claim-Provider:", len(claim_provider_links))
        print("Total edges:", len(rows))

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 13. MAIN EXECUTION MENU
# =====================================================

if __name__ == "__main__":

    print("\nINSURANCE FRAUD DATA GENERATOR")

    print("\n1. Generate base data")
    print("2. Generate claims")
    print("3. Generate invoices")
    print("4. Generate payments")
    print("5. Generate relationship edges")

    choice = input("\nEnter your choice (1-5): ").strip()

    if choice == "1":

        generate_base_data()

    elif choice == "2":

        generate_claims()

    elif choice == "3":

        generate_invoices()

    elif choice == "4":

        generate_payments()

    elif choice == "5":

        generate_relationship_edges()

    else:

        print("Invalid choice. Please enter 1-5.")
