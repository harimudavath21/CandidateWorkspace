# ClaimShield - Insurance Fraud Detection & Investigation System

## 1. Project Overview

ClaimShield is an insurance fraud detection and investigation system designed to identify suspicious insurance claims using rule-based anomaly detection, risk scoring, relationship analysis, and investigation management.

The system analyzes claim, claimant, policy, provider, invoice, payment, and relationship data to identify unusual patterns and generate risk indicators. It provides investigators with a centralized dashboard to review suspicious claims, manage investigations, track evidence, and maintain audit records.

**Project Name:** ClaimShield  
**Domain:** Insurance Analytics, Fraud Detection, Artificial Intelligence and Data Analytics  
**Application:** Interactive Streamlit Dashboard  
**Database:** MySQL

## 2. Problem Statement

Insurance fraud can cause financial losses through suspicious claims, duplicate invoices, invalid policy references, payment discrepancies, and unusual relationships between claimants and service providers.

Manual verification of large volumes of insurance claims is time-consuming and can make suspicious patterns difficult to identify.

ClaimShield addresses this problem by automating anomaly detection, assigning risk scores, analyzing entity relationships, and supporting structured investigations.

## 3. Project Objectives

- Identify suspicious insurance claim patterns.
- Detect duplicate invoice numbers and payment discrepancies.
- Identify invalid policy and provider references.
- Detect shared contact information across claimants.
- Calculate claim-level risk scores.
- Analyze relationships between insurance entities.
- Support investigation assignment and status tracking.
- Register and manage investigation evidence.
- Maintain audit logs for important activities.
- Provide an interactive dashboard for monitoring fraud indicators and investigations.

## 4. Key Features

### 4.1 Fraud Detection

The system implements five rule-based detection mechanisms:

1. Invalid Policy Reference Detection
2. Duplicate Invoice Detection
3. Payment Overstatement Detection
4. Shared Contact Pattern Detection
5. Invalid Provider Relationship Detection

### 4.2 Risk Scoring

Claims receive a risk score based on detected indicators.

| Indicator | Risk Points |
|---|---:|
| Payment Overstatement | 40 |
| Invalid Policy Reference | 30 |
| Invalid Provider Relationship | 25 |
| Duplicate Invoice | 25 |
| Shared Contact Pattern | 10 |

**Risk categories:**

- LOW: 0-19
- MEDIUM: 20-39
- HIGH: 40-69
- CRITICAL: 70-100

### 4.3 Investigation Management

- Create investigations for claims with detected indicators.
- Assign investigators.
- Track investigation status and priority.
- Maintain investigation event history.
- Record status changes in audit logs.

### 4.4 Evidence Management

- Register investigation evidence.
- Track evidence status.
- Review and verify evidence.
- Maintain evidence-related audit records.

### 4.5 Graph Analytics

Uses NetworkX to analyze relationships between claimants, policies, incidents, providers, and other entities.

The analysis includes:

- Entity relationship network construction.
- Degree centrality.
- Connected component analysis.
- Identification of highly connected entities.

### 4.6 Data Quality Validation

Validates database records and identifies:

- Missing references.
- Duplicate invoice groups.
- Payment discrepancies.
- Shared contact patterns.
- Invalid provider relationships.

### 4.7 Interactive Dashboard

The Streamlit dashboard includes:

1. Dashboard Overview
2. Fraud Analytics
3. Investigation Management
4. Evidence Management
5. Graph Analytics
6. Data Quality

## 5. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Database | MySQL |
| Data Processing | Pandas, NumPy |
| Data Generation | Faker |
| Graph Analytics | NetworkX |
| Dashboard | Streamlit |
| Visualization | Plotly |
| Testing | Pytest |
| Database Connectivity | MySQL Connector |
| Configuration | Python Dotenv |

## 6. System Architecture

```text
                 Insurance Data
                       |
                       v
               Data Generation
                       |
                       v
                MySQL Database
                       |
                       v
               Data Validation
                       |
                       v
              Fraud Detection
                       |
                       v
                 Risk Scoring
                       |
             +---------+---------+
             |                   |
             v                   v
       Graph Analytics     Investigations
                                 |
                                 v
                         Evidence Management
                                 |
                                 v
                            Audit Logs
                                 |
                                 v
                       Streamlit Dashboard
                                 |
                                 v
                        Reports and Exports
```

## 7. Database Design

The project uses MySQL with 15 tables:

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

The database maintains relationships between insurance entities and supports fraud analysis, investigation tracking, and auditability.

## 8. Dataset Information

The project uses synthetically generated insurance data.

| Entity | Records |
|---|---:|
| Claimants | 2,000 |
| Policies | 2,000 |
| Incidents | 5,000 |
| Providers | 500 |
| Claims | 5,000 |
| Invoices | 5,000 |
| Payments | 5,000 |
| Relationship Edges | 8,000 |

A controlled set of anomalies was injected into the dataset to test the detection mechanisms.

## 9. Detection and Evaluation Results

The detection engine identified 10 indicators across the controlled anomalies.

| Indicator Type | Detected Records |
|---|---:|
| Invalid Policy Reference | 1 |
| Duplicate Invoice | 2 |
| Payment Overstatement | 1 |
| Shared Contact Pattern | 5 |
| Invalid Provider Relationship | 1 |
| **Total** | **10** |

### 9.1 Risk Distribution

| Risk Category | Claims |
|---|---:|
| LOW | 4,995 |
| MEDIUM | 4 |
| HIGH | 1 |
| CRITICAL | 0 |

### 9.2 Controlled Evaluation Results

| Metric | Result |
|---|---:|
| Precision | 1.00 |
| Recall | 1.00 |
| F1-Score | 1.00 |
| Accuracy | 1.00 |
| True Positives | 10 |
| False Positives | 0 |
| True Negatives | 4,990 |
| False Negatives | 0 |

**Important:** These evaluation results are based on controlled anomalies injected into synthetic data. They demonstrate detection performance against the designed test cases and should not be interpreted as real-world insurance fraud detection accuracy.

A shared contact or other risk indicator is a reason for further investigation, not proof of fraud.

## 10. Project Structure

```text
CandidateWorkspace/
|
|-- app.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- DATA_DICTIONARY.md
|-- REPRODUCIBILITY.md
|-- .env
|-- .gitignore
|
|-- data/
|   |-- ground_truth.csv
|
|-- exports/
|   |-- csv/
|   |-- json/
|   |-- sql/
|   |-- export_manifest.json
|
|-- reports/
|   |-- evaluation_metrics.csv
|   |-- confusion_matrix.csv
|   |-- graph_node_analysis.csv
|   |-- graph_edge_analysis.csv
|
|-- src/
|   |-- detection.py
|   |-- evaluation.py
|   |-- generator.py
|   |-- scoring.py
|   |-- storage.py
|   |-- validation.py
|   |-- workflow.py
|   |-- anomaly_generator.py
|   |-- graph_analysis.py
|   |-- investigation_lifecycle.py
|   |-- evidence_management.py
|   |-- export_manager.py
|
|-- tests/
    |-- test_detection.py
    |-- test_generator.py
    |-- test_validation.py
```

## 11. Installation and Setup

### Prerequisites

- Python 3.10 or later
- MySQL Server
- MySQL Workbench (optional)
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone <your-github-repository-url>
cd CandidateWorkspace
```

### Step 2: Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=hackathon
```

Replace the password placeholder with your local MySQL password. Do not commit `.env` to GitHub.

### Step 5: Prepare the Database

Create the MySQL database if it does not already exist:

```sql
CREATE DATABASE hackathon;
```

Ensure the required tables and project data are initialized before running the application.

**Note:** The existing project database is already populated. Do not rerun data generators against it unless you intentionally plan to reset the dataset.

### Step 6: Run the Dashboard

```bash
streamlit run app.py
```

The Streamlit application will open in your browser.

## 12. Running Automated Tests

Execute the test suite:

```bash
python -m pytest tests/ -v
```

**Verified test result: 34 tests passed.**

## 13. Data Exports and Backup

ClaimShield supports exporting database tables into CSV and JSON formats.

It also generates a MySQL SQL backup.

The backup was restored into a separate test database, and all 15 tables and their record counts were verified successfully.

## 14. Reproducibility

The project uses a configured random seed:

`20261115`

Dataset generation settings, anomaly injection, risk thresholds, evaluation methodology, and setup instructions are documented in `REPRODUCIBILITY.md`.

## 15. Future Enhancements

- Introduce machine learning models for fraud risk prediction.
- Apply supervised classification when reliable labeled historical data is available.
- Use graph-based anomaly detection to identify complex fraud networks.
- Integrate real-time claim processing.
- Add role-based access control for investigators and administrators.
- Introduce explainable AI techniques to improve risk-score transparency.
- Evaluate models on representative, independently labeled real-world datasets.

## 16. Conclusion

ClaimShield demonstrates an integrated insurance fraud detection and investigation workflow. It combines data validation, rule-based anomaly detection, risk scoring, graph analytics, investigation lifecycle management, evidence tracking, audit logging, and interactive visualization.

The project provides a foundation for identifying suspicious insurance claim patterns and supporting structured investigation workflows.

---

**ClaimShield - Detect Suspicious Patterns. Support Better Investigations.**