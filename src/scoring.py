
from src.storage import get_connection


def classify_risk(score):
    """Convert numerical risk score into a category."""

    if score >= 70:
        return "CRITICAL"
    elif score >= 40:
        return "HIGH"
    elif score >= 20:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_claim_risk():
    """Calculate aggregated risk scores for all claims."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Fetch all claims
        cursor.execute("""
            SELECT claim_id
            FROM claims
            ORDER BY claim_id
        """)

        claims = cursor.fetchall()

        # Fetch detection indicators
        cursor.execute("""
            SELECT
                claim_id,
                indicator_type,
                risk_score
            FROM fraud_indicators
            ORDER BY claim_id
        """)

        indicators = cursor.fetchall()

        # Group indicators by claim
        claim_indicators = {}

        for claim_id, indicator_type, risk_score in indicators:

            if claim_id not in claim_indicators:
                claim_indicators[claim_id] = []

            claim_indicators[claim_id].append(
                (indicator_type, float(risk_score))
            )

        rows = []

        for (claim_id,) in claims:

            findings = claim_indicators.get(claim_id, [])

            # Calculate total risk
            raw_score = sum(
                score for _, score in findings
            )

            total_score = min(raw_score, 100)

            risk_category = classify_risk(total_score)

            indicator_count = len(findings)

            # Explain the detected risk
            explanations = sorted({
                indicator_type
                for indicator_type, _ in findings
            })

            explanation = (
                ", ".join(explanations)
                if explanations
                else "No suspicious indicators detected"
            )

            rows.append((
                claim_id,
                total_score,
                risk_category,
                indicator_count,
                explanation,
            ))

        # Store risk scores
        cursor.executemany(
            """
            INSERT INTO claim_risk_scores (
                claim_id,
                total_risk_score,
                risk_category,
                indicator_count,
                risk_explanation
            )
            VALUES (%s, %s, %s, %s, %s)

            ON DUPLICATE KEY UPDATE
                total_risk_score = VALUES(total_risk_score),
                risk_category = VALUES(risk_category),
                indicator_count = VALUES(indicator_count),
                risk_explanation = VALUES(risk_explanation),
                scored_at = CURRENT_TIMESTAMP
            """,
            rows,
        )

        connection.commit()

        print("\nCLAIM RISK SCORING COMPLETED")
        print("Total claims scored:", len(rows))

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def show_risk_summary():

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT
                risk_category,
                COUNT(*) AS total_claims,
                ROUND(AVG(total_risk_score), 2)
                    AS average_score
            FROM claim_risk_scores
            GROUP BY risk_category
            ORDER BY
                FIELD(
                    risk_category,
                    'CRITICAL',
                    'HIGH',
                    'MEDIUM',
                    'LOW'
                )
        """)

        results = cursor.fetchall()

        print("\nCLAIM RISK SUMMARY")
        print("=" * 55)

        for category, count, average in results:

            print(
                f"{category}: "
                f"{count} claims | "
                f"Average score: {average}"
            )

        print("=" * 55)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":

    calculate_claim_risk()
    show_risk_summary()
