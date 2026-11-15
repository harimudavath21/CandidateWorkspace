
import csv

from config import DATA_DIR, REPORTS_DIR
from src.storage import get_connection


GROUND_TRUTH_FILE = DATA_DIR / "ground_truth.csv"


# =====================================================
# 1. LOAD GROUND TRUTH AND MAP TO CLAIMS
# =====================================================

def load_ground_truth_claims(cursor):
    """
    Convert ground-truth entities into affected claim IDs.

    Ground truth is used only for evaluation.
    It is never used by the detection engine.
    """

    if not GROUND_TRUTH_FILE.exists():
        raise FileNotFoundError(
            f"Ground truth file not found: {GROUND_TRUTH_FILE}"
        )

    positive_claims = set()

    with open(
        GROUND_TRUTH_FILE,
        "r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "anomaly_id",
            "entity_type",
            "entity_id",
            "anomaly_type",
            "expected_label",
        }

        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError(
                "Ground truth CSV has missing columns"
            )

        for record in reader:

            if record["expected_label"] != "SUSPICIOUS":
                continue

            entity_type = record["entity_type"]
            entity_id = record["entity_id"]

            # -----------------------------------------
            # CLAIM
            # -----------------------------------------

            if entity_type == "CLAIM":

                cursor.execute("""
                    SELECT claim_id
                    FROM claims
                    WHERE claim_id = %s
                """, (entity_id,))

                result = cursor.fetchone()

                if result is None:
                    raise ValueError(
                        f"Ground-truth claim not found: {entity_id}"
                    )

                positive_claims.add(result[0])

            # -----------------------------------------
            # INVOICE
            # -----------------------------------------

            elif entity_type == "INVOICE":

                cursor.execute("""
                    SELECT invoice_id
                    FROM invoices
                    WHERE invoice_record_id = %s
                """, (int(entity_id),))

                result = cursor.fetchone()

                if result is None:
                    raise ValueError(
                        f"Ground-truth invoice not found: {entity_id}"
                    )

                invoice_number = result[0]

                cursor.execute("""
                    SELECT DISTINCT claim_id
                    FROM invoices
                    WHERE invoice_id = %s
                """, (invoice_number,))

                for row in cursor.fetchall():
                    positive_claims.add(row[0])

            # -----------------------------------------
            # PAYMENT
            # -----------------------------------------

            elif entity_type == "PAYMENT":

                cursor.execute("""
                    SELECT claim_id
                    FROM payments
                    WHERE payment_id = %s
                """, (entity_id,))

                result = cursor.fetchone()

                if result is None:
                    raise ValueError(
                        f"Ground-truth payment not found: {entity_id}"
                    )

                positive_claims.add(result[0])

            # -----------------------------------------
            # CLAIMANT
            # -----------------------------------------

            elif entity_type == "CLAIMANT":

                # Use the same representative claim
                # selected by the detection engine.
                cursor.execute("""
                    SELECT MIN(claim_id)
                    FROM claims
                    WHERE claimant_id = %s
                """, (entity_id,))

                result = cursor.fetchone()

                if result is None or result[0] is None:
                    raise ValueError(
                        f"No claims found for claimant: {entity_id}"
                    )

                positive_claims.add(result[0])

            # -----------------------------------------
            # RELATIONSHIP EDGE
            # -----------------------------------------

            elif entity_type == "RELATIONSHIP_EDGE":

                cursor.execute("""
                    SELECT source_entity_id
                    FROM relationship_edges
                    WHERE edge_id = %s
                      AND source_entity_type = 'CLAIM'
                """, (entity_id,))

                result = cursor.fetchone()

                if result is None:
                    raise ValueError(
                        f"Ground-truth relationship edge "
                        f"not found: {entity_id}"
                    )

                positive_claims.add(result[0])

            else:

                raise ValueError(
                    f"Unsupported ground-truth entity type: "
                    f"{entity_type}"
                )

    return positive_claims


# =====================================================
# 2. LOAD DETECTED CLAIMS
# =====================================================

def load_detected_claims(cursor):
    """Get unique claims flagged by the detection engine."""

    cursor.execute("""
        SELECT DISTINCT claim_id
        FROM fraud_indicators
    """)

    return {
        row[0]
        for row in cursor.fetchall()
    }


# =====================================================
# 3. CALCULATE EVALUATION METRICS
# =====================================================

def calculate_metrics(all_claims, actual, predicted):
    """Calculate binary classification metrics."""

    true_positives = len(actual & predicted)

    false_positives = len(predicted - actual)

    false_negatives = len(actual - predicted)

    true_negatives = len(
        all_claims - (actual | predicted)
    )

    precision = (
        true_positives /
        (true_positives + false_positives)
        if true_positives + false_positives else 0
    )

    recall = (
        true_positives /
        (true_positives + false_negatives)
        if true_positives + false_negatives else 0
    )

    f1_score = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0
    )

    accuracy = (
        (true_positives + true_negatives) /
        len(all_claims)
        if all_claims else 0
    )

    return {
        "total_claims": len(all_claims),
        "actual_positive": len(actual),
        "predicted_positive": len(predicted),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "accuracy": accuracy,
    }


# =====================================================
# 4. SAVE EVALUATION REPORTS
# =====================================================

def save_evaluation_reports(metrics):
    """Save metrics and confusion matrix as CSV files."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics_file = REPORTS_DIR / "evaluation_metrics.csv"

    confusion_file = REPORTS_DIR / "confusion_matrix.csv"

    # -----------------------------------------
    # Evaluation metrics
    # -----------------------------------------

    with open(
        metrics_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(["Metric", "Value"])

        for key, value in metrics.items():
            writer.writerow([key, value])

    # -----------------------------------------
    # Confusion matrix
    # -----------------------------------------

    with open(
        confusion_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "Actual / Predicted",
            "Fraud",
            "Normal"
        ])

        writer.writerow([
            "Fraud",
            metrics["true_positives"],
            metrics["false_negatives"],
        ])

        writer.writerow([
            "Normal",
            metrics["false_positives"],
            metrics["true_negatives"],
        ])

    print("\nREPORT FILES SAVED")

    print("Metrics:", metrics_file)

    print("Confusion matrix:", confusion_file)


# =====================================================
# 5. DISPLAY EVALUATION RESULTS
# =====================================================

def display_evaluation_results(metrics):

    print("\nEVALUATION RESULTS")
    print("=" * 55)

    for key, value in metrics.items():

        if isinstance(value, float):
            print(f"{key}: {value:.4f}")

        else:
            print(f"{key}: {value}")

    print("\nCONFUSION MATRIX")
    print("=" * 55)

    print(
        f"{'Actual / Predicted':<22}"
        f"{'Fraud':>10}"
        f"{'Normal':>12}"
    )

    print("-" * 44)

    print(
        f"{'Fraud':<22}"
        f"{metrics['true_positives']:>10}"
        f"{metrics['false_negatives']:>12}"
    )

    print(
        f"{'Normal':<22}"
        f"{metrics['false_positives']:>10}"
        f"{metrics['true_negatives']:>12}"
    )

    print("=" * 55)


# =====================================================
# 6. MAIN EVALUATION FUNCTION
# =====================================================

def run_evaluation():
    """Run the complete fraud detection evaluation."""

    connection = get_connection()
    cursor = connection.cursor()

    try:

        print("\nINSURANCE FRAUD MODEL EVALUATION")
        print("=" * 55)

        # -----------------------------------------
        # Load all claims
        # -----------------------------------------

        cursor.execute("""
            SELECT claim_id
            FROM claims
        """)

        all_claims = {
            row[0]
            for row in cursor.fetchall()
        }

        if not all_claims:
            raise ValueError(
                "No claims available for evaluation"
            )

        # -----------------------------------------
        # Load ground truth
        # -----------------------------------------

        actual = load_ground_truth_claims(cursor)

        # -----------------------------------------
        # Load detection predictions
        # -----------------------------------------

        predicted = load_detected_claims(cursor)

        # -----------------------------------------
        # Validate evaluation population
        # -----------------------------------------

        if not actual.issubset(all_claims):
            raise ValueError(
                "Ground-truth claims are outside "
                "the evaluation population"
            )

        if not predicted.issubset(all_claims):
            raise ValueError(
                "Detected claims are outside "
                "the evaluation population"
            )

        # -----------------------------------------
        # Calculate metrics
        # -----------------------------------------

        metrics = calculate_metrics(
            all_claims,
            actual,
            predicted
        )

        # -----------------------------------------
        # Display results
        # -----------------------------------------

        display_evaluation_results(metrics)

        # -----------------------------------------
        # Save reports
        # -----------------------------------------

        save_evaluation_reports(metrics)

        print("\nEVALUATION COMPLETED SUCCESSFULLY")

    finally:

        cursor.close()
        connection.close()


# =====================================================
# 7. EXECUTION
# =====================================================

if __name__ == "__main__":

    run_evaluation()
