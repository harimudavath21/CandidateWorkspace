
# ClaimShield — Reproducibility Documentation

## 1. Project Overview

ClaimShield is an insurance fraud detection and investigation system.

It combines:
- Synthetic insurance data generation
- Controlled anomaly injection
- Rule-based fraud detection
- Claim risk scoring
- Investigation lifecycle management
- Evidence management and audit logging
- Graph-based relationship analysis
- Data quality validation
- Interactive Streamlit dashboard
- CSV, JSON and SQL exports

## 2. Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Database | MySQL |
| Database Connectivity | mysql-connector-python |
| Data Processing | Pandas, NumPy |
| Synthetic Data Generation | Faker |
| Graph Analytics | NetworkX |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |
| Configuration | python-dotenv |

## 3. Reproducibility Configuration

The project uses a fixed random seed.

| Configuration | Value |
|---|---:|
| Random Seed | 20261115 |
| Claimants | 2,000 |
| Policies | 2,000 |
| Incidents | 5,000 |
| Providers | 500 |
| Claims | 5,000 |
| Relationship Edges | 8,000 |

The configuration is maintained in `config.py`.

A fixed seed helps make random data generation repeatable when the same generation logic, dependencies and initial conditions are used.

## 4. Database Configuration

Database configuration is maintained through environment variables in `.env`.

Required settings:

- DB_HOST
- DB_PORT
- DB_USER
- DB_PASSWORD
- DB_NAME

The `.env` file must not be committed to version control.

The database name used in this project is `hackathon`.

## 5. Dataset Overview

The project contains the following database tables:

1. claimants
2. policies
3. incidents
4. providers
5. claims
6. invoices
7. payments
8. relationship_edges
9. fraud_indicators
10. claim_risk_scores
11. investigations
12. investigation_events
13. audit_logs
14. data_quality_issues
15. investigation_evidence

The generated dataset contains 2,000 claimants, 5,000 claims, 5,000 invoices, 5,000 payments and 8,000 relationship edges, along with supporting records.

## 6. Controlled Anomaly Injection

Five controlled anomaly scenarios were introduced to validate the detection pipeline.

| Scenario | Description |
|---|---|
| Invalid Policy Reference | A claim contains a missing policy reference after an invalid reference was recorded as a data quality issue. |
| Duplicate Invoice | Two claims share the same invoice number. |
| Payment Overstatement | A payment exceeds the approved claim amount. |
| Shared Contact Pattern | Five claimants share the same phone number. |
| Invalid Provider Relationship | A relationship edge references a provider that does not exist. |

The ground-truth labels are stored in:

`data/ground_truth.csv`

There are nine ground-truth entity records across these scenarios.

Shared contact information is treated as a suspicious signal, not proof of fraud.

## 7. Fraud Detection Rules

The detection engine implements five rule categories:

1. INVALID_POLICY_REFERENCE
2. DUPLICATE_INVOICE
3. PAYMENT_OVERSTATEMENT
4. SHARED_CONTACT_PATTERN
5. INVALID_PROVIDER_RELATIONSHIP

Detected indicators are stored in the `fraud_indicators` table.

## 8. Risk Scoring Methodology

The risk scoring engine assigns points to detected indicators.

| Indicator | Risk Points |
|---|---:|
| Payment Overstatement | 40 |
| Invalid Policy Reference | 30 |
| Invalid Provider Relationship | 25 |
| Duplicate Invoice | 25 |
| Shared Contact Pattern | 10 |

The total claim risk score is capped at 100.

### Risk Categories

| Score Range | Risk Category |
|---|---|
| 0–19 | LOW |
| 20–39 | MEDIUM |
| 40–69 | HIGH |
| 70–100 | CRITICAL |

The risk score is an investigation prioritization signal. It is not a determination of fraud.

## 9. Evaluation Methodology

The evaluation module compares detected claim-level results with the controlled ground-truth dataset.

It calculates:

- True Positives
- False Positives
- True Negatives
- False Negatives
- Precision
- Recall
- F1 Score
- Accuracy

### Recorded Evaluation Results

| Metric | Result |
|---|---:|
| Total Claims | 5,000 |
| Actual Positive | 10 |
| Predicted Positive | 10 |
| True Positives | 10 |
| False Positives | 0 |
| True Negatives | 4,990 |
| False Negatives | 0 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 Score | 1.0000 |
| Accuracy | 1.0000 |

### Evaluation Limitation

These results were obtained using synthetic data with deliberately injected anomalies.

They demonstrate that the implemented detection rules identified the planted test cases under the current evaluation mapping.

They do not establish real-world fraud detection accuracy or generalization to actual insurance claims.

Real-world validation would require representative historical data, independently verified labels, and testing on unseen claims.

## 10. Investigation and Evidence Management

The investigation workflow creates investigation records for claims with detected indicators.

It supports:

- Investigator assignment
- Investigation status updates
- Investigation event history
- Evidence registration
- Evidence status updates
- Audit logging

Investigation and evidence changes are recorded for traceability.

## 11. Graph Analytics

NetworkX is used to analyze relationships between insurance entities.

The graph analysis currently processes:

- 8,000 relationship edges
- 10,501 graph nodes
- 2,501 connected components

The analysis calculates degree centrality and connected components.

Graph relationships are useful for identifying connected entities and unusual relationship patterns. A connection alone does not prove fraudulent activity.

## 12. Data Export and Backup

The export module creates:

- CSV files in `exports/csv/`
- JSON files in `exports/json/`
- MySQL SQL backup in `exports/sql/`
- Export verification manifest in `exports/export_manifest.json`

All 15 database tables passed CSV and JSON row-count verification.

The SQL backup was created successfully. A separate database restoration test is still required to verify recovery.

## 13. Project Reports

Generated reports are stored in `reports/`.

- evaluation_metrics.csv
- confusion_matrix.csv
- graph_node_analysis.csv
- graph_edge_analysis.csv

## 14. Environment and Dependency Reproducibility

The project uses a Python virtual environment.

The installed dependency versions verified during development include:

| Package | Version |
|---|---|
| pandas | 3.1.1 |
| numpy | 2.5.4 |
| Faker | 40.54.0 |
| networkx | 3.7 |
| streamlit | 1.67.0 |
| plotly | 7.1.0 |
| pytest | 9.2.0 |
| mysql-connector-python | 26.10.0 |
| python-dotenv | 1.2.4 |

Python version used during development: 3.14.6.

For repeatable environments, retain the dependency versions in `requirements.txt`.

## 15. Reproducibility Considerations

To reproduce the project:

1. Use a compatible Python environment.
2. Install the project dependencies.
3. Configure the MySQL connection through `.env`.
4. Create the required database and tables.
5. Use the configured random seed.
6. Follow the project's data generation and anomaly injection workflow.
7. Execute detection, scoring and evaluation.
8. Run investigation and evidence workflows.
9. Generate graph analysis and dashboard reports.
10. Run the export module and verify the exported records.

Avoid rerunning data generators against an already populated database unless a database reset and regeneration plan is in place.

## 16. Project Conclusion

ClaimShield demonstrates an end-to-end insurance fraud detection and investigation workflow using synthetic insurance data.

It combines data engineering, rule-based anomaly detection, risk scoring, graph analytics, investigation tracking, evidence management, database auditing and interactive visualization.

The current implementation is a controlled prototype intended for demonstration and further validation with real-world insurance data.
