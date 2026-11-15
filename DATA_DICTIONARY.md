# ClaimShield — Database Data Dictionary

## 1. Database Overview

**Database name:** `hackathon`  
**Database system:** MySQL  
**Project:** ClaimShield — Insurance Fraud Detection and Investigation System  
**Total tables:** 15

This document describes the database schema used by ClaimShield. It includes claimant, policy, incident, claim, provider, invoice, payment, fraud detection, risk scoring, investigation, evidence, audit, and data-quality information.

## 2. Table Summary

| Table | Purpose |
|---|---|
| claimants | Stores claimant personal and contact information |
| providers | Stores service provider information |
| policies | Stores insurance policy details |
| incidents | Stores reported incident information |
| claims | Stores insurance claims and claim amounts |
| invoices | Stores invoices associated with claims and providers |
| payments | Stores payment transactions |
| relationship_edges | Stores relationships between entities for graph analysis |
| fraud_indicators | Stores detected suspicious patterns |
| claim_risk_scores | Stores calculated claim risk scores |
| investigations | Stores investigation assignments and status |
| investigation_events | Maintains investigation event history |
| investigation_evidence | Stores evidence associated with investigations |
| audit_logs | Records changes and actions performed in the system |
| data_quality_issues | Records detected data-quality problems |

## 3. Detailed Table Structures

### 3.1 claimants

**Purpose:** Stores claimant information.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| claimant_id | VARCHAR(30) | No | PK | Unique claimant identifier |
| full_name | VARCHAR(150) | No | | Claimant full name |
| age | INT | Yes | | Claimant age |
| gender | VARCHAR(20) | Yes | | Gender information |
| address | VARCHAR(255) | Yes | | Residential address |
| city | VARCHAR(100) | Yes | | City |
| phone | VARCHAR(20) | Yes | | Contact number |
| email | VARCHAR(150) | Yes | | Email address |
| created_at | DATETIME | Yes | | Record creation timestamp |

### 3.2 providers

**Purpose:** Stores insurance-related service provider information.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| provider_id | VARCHAR(30) | No | PK | Unique provider identifier |
| provider_name | VARCHAR(150) | Yes | | Provider name |
| provider_type | VARCHAR(80) | Yes | | Provider category |
| address | VARCHAR(255) | Yes | | Provider address |
| phone | VARCHAR(20) | Yes | | Provider contact number |
| registration_date | DATE | Yes | | Registration date |

### 3.3 policies

**Purpose:** Stores insurance policy information associated with claimants.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| policy_id | VARCHAR(30) | No | PK | Unique policy identifier |
| claimant_id | VARCHAR(30) | No | MUL | Associated claimant |
| policy_type | VARCHAR(50) | Yes | | Insurance policy type |
| start_date | DATE | Yes | | Policy start date |
| end_date | DATE | Yes | | Policy expiry date |
| premium_amount | DECIMAL(12,2) | Yes | | Premium amount |
| coverage_amount | DECIMAL(12,2) | Yes | | Insurance coverage amount |
| policy_status | VARCHAR(30) | Yes | | Current policy status |

### 3.4 incidents

**Purpose:** Stores details of reported incidents.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| incident_id | VARCHAR(30) | No | PK | Unique incident identifier |
| incident_type | VARCHAR(50) | Yes | | Type of incident |
| incident_date | DATE | Yes | | Date of incident |
| incident_location | VARCHAR(255) | Yes | | Incident location |
| description | TEXT | Yes | | Incident description |
| estimated_damage | DECIMAL(12,2) | Yes | | Estimated financial damage |

### 3.5 claims

**Purpose:** Stores insurance claim records and their financial details.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| claim_id | VARCHAR(30) | No | PK | Unique claim identifier |
| claimant_id | VARCHAR(30) | No | MUL | Claimant associated with claim |
| policy_id | VARCHAR(30) | Yes | MUL | Related insurance policy |
| incident_id | VARCHAR(30) | Yes | MUL | Related incident |
| claim_date | DATE | Yes | | Claim submission date |
| claimed_amount | DECIMAL(12,2) | Yes | | Amount requested |
| approved_amount | DECIMAL(12,2) | Yes | | Amount approved |
| claim_status | VARCHAR(30) | Yes | | Current claim status |
| description | TEXT | Yes | | Claim description |

### 3.6 invoices

**Purpose:** Stores invoice records associated with claims and providers.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| invoice_record_id | BIGINT | No | PK | Auto-increment invoice record identifier |
| invoice_id | VARCHAR(100) | No | MUL | Invoice reference number |
| claim_id | VARCHAR(30) | Yes | MUL | Associated claim |
| provider_id | VARCHAR(30) | Yes | MUL | Associated provider |
| invoice_date | DATE | Yes | | Invoice date |
| invoice_amount | DECIMAL(12,2) | Yes | | Invoice amount |
| description | TEXT | Yes | | Invoice description |

### 3.7 payments

**Purpose:** Stores payment transactions related to claims.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| payment_id | VARCHAR(40) | No | PK | Unique payment identifier |
| claim_id | VARCHAR(30) | No | MUL | Associated claim |
| payment_date | DATE | Yes | | Payment date |
| payment_amount | DECIMAL(12,2) | Yes | | Payment amount |
| payment_status | VARCHAR(30) | Yes | | Payment status |
| payment_method | VARCHAR(30) | Yes | | Payment method |

### 3.8 relationship_edges

**Purpose:** Stores entity relationships used in relationship and graph analysis.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| edge_id | VARCHAR(40) | No | PK | Unique relationship identifier |
| source_entity_type | VARCHAR(30) | No | MUL | Source entity category |
| source_entity_id | VARCHAR(100) | No | | Source entity identifier |
| target_entity_type | VARCHAR(30) | No | MUL | Target entity category |
| target_entity_id | VARCHAR(100) | No | | Target entity identifier |
| relationship_type | VARCHAR(80) | Yes | | Type of relationship |
| weight | DECIMAL(5,2) | Yes | | Relationship weight |
| created_at | DATETIME | Yes | | Relationship creation timestamp |

### 3.9 fraud_indicators

**Purpose:** Stores suspicious patterns detected by fraud detection rules.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| indicator_id | VARCHAR(40) | No | PK | Unique indicator identifier |
| claim_id | VARCHAR(30) | No | MUL | Associated claim |
| indicator_type | VARCHAR(100) | No | | Detected fraud indicator category |
| indicator_description | TEXT | Yes | | Explanation of detected pattern |
| severity | VARCHAR(20) | Yes | | Indicator severity |
| risk_score | DECIMAL(5,2) | Yes | | Risk points assigned |
| detected_at | DATETIME | Yes | | Detection timestamp |

### 3.10 claim_risk_scores

**Purpose:** Stores aggregated risk scores and classifications for claims.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| claim_id | VARCHAR(30) | No | PK | Unique claim identifier |
| total_risk_score | DECIMAL(5,2) | No | | Calculated total risk score |
| risk_category | VARCHAR(20) | No | | Risk classification |
| indicator_count | INT | Yes | | Number of associated indicators |
| risk_explanation | TEXT | Yes | | Explanation of calculated risk |
| scored_at | DATETIME | Yes | | Scoring timestamp |

### 3.11 investigations

**Purpose:** Stores investigation assignments, priorities, statuses, and notes.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| investigation_id | VARCHAR(40) | No | PK | Unique investigation identifier |
| claim_id | VARCHAR(30) | No | MUL | Claim under investigation |
| assigned_investigator | VARCHAR(100) | Yes | | Assigned investigator |
| investigation_status | VARCHAR(30) | Yes | | Current investigation status |
| priority | VARCHAR(20) | Yes | | Investigation priority |
| risk_score | DECIMAL(5,2) | Yes | | Associated risk score |
| opened_at | DATETIME | Yes | | Investigation opening timestamp |
| closed_at | DATETIME | Yes | | Investigation closing timestamp |
| investigation_notes | TEXT | Yes | | Investigation notes |

### 3.12 investigation_events

**Purpose:** Maintains a chronological history of investigation activities.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| event_id | VARCHAR(40) | No | PK | Unique event identifier |
| investigation_id | VARCHAR(40) | No | MUL | Associated investigation |
| event_type | VARCHAR(80) | Yes | | Event category |
| event_description | TEXT | Yes | | Event details |
| event_timestamp | DATETIME | Yes | | Event timestamp |
| performed_by | VARCHAR(100) | Yes | | Person performing the event |

### 3.13 investigation_evidence

**Purpose:** Stores evidence references and review status for investigations.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| evidence_id | VARCHAR(40) | No | PK | Unique evidence identifier |
| investigation_id | VARCHAR(40) | No | MUL | Associated investigation |
| evidence_type | VARCHAR(80) | No | | Evidence category |
| evidence_reference | VARCHAR(255) | No | | Evidence reference |
| evidence_description | TEXT | Yes | | Evidence details |
| collected_by | VARCHAR(100) | No | | Person collecting evidence |
| collected_at | DATETIME | Yes | | Collection timestamp |
| evidence_status | VARCHAR(30) | Yes | | Current evidence status |

### 3.14 audit_logs

**Purpose:** Maintains an audit trail of actions and changes performed in the system.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| audit_id | BIGINT | No | PK | Auto-increment audit identifier |
| entity_type | VARCHAR(50) | No | MUL | Type of entity affected |
| entity_id | VARCHAR(100) | No | | Identifier of affected entity |
| action | VARCHAR(80) | No | | Action performed |
| old_value | JSON | Yes | | Previous value |
| new_value | JSON | Yes | | Updated value |
| performed_by | VARCHAR(100) | Yes | | Person performing the action |
| performed_at | DATETIME | Yes | | Action timestamp |

### 3.15 data_quality_issues

**Purpose:** Records invalid or inconsistent data detected during validation.

| Column | Data Type | Nullable | Key | Description |
|---|---|---|---|---|
| issue_id | BIGINT | No | PK | Auto-increment issue identifier |
| entity_type | VARCHAR(50) | No | | Affected entity category |
| entity_id | VARCHAR(100) | No | | Affected entity identifier |
| field_name | VARCHAR(100) | Yes | | Field containing the issue |
| invalid_value | VARCHAR(255) | Yes | | Detected invalid value |
| issue_type | VARCHAR(100) | Yes | | Data-quality issue category |
| issue_description | TEXT | Yes | | Explanation of the issue |
| detected_at | DATETIME | Yes | | Detection timestamp |
| resolution_status | VARCHAR(30) | Yes | | Resolution status; default OPEN |

## 4. Logical Relationships

The following relationships are represented by the database column structure:

- `claimants.claimant_id` — `policies.claimant_id`
- `claimants.claimant_id` — `claims.claimant_id`
- `policies.policy_id` — `claims.policy_id`
- `incidents.incident_id` — `claims.incident_id`
- `claims.claim_id` — `invoices.claim_id`
- `providers.provider_id` — `invoices.provider_id`
- `claims.claim_id` — `payments.claim_id`
- `claims.claim_id` — `fraud_indicators.claim_id`
- `claims.claim_id` — `claim_risk_scores.claim_id`
- `claims.claim_id` — `investigations.claim_id`
- `investigations.investigation_id` — `investigation_events.investigation_id`
- `investigations.investigation_id` — `investigation_evidence.investigation_id`

The `relationship_edges` table stores source and target entity references for graph analysis. The `audit_logs` table stores entity-level action history.

**Note:** These are logical relationships inferred from the column names and indexed fields. An indexed field (`MUL`) does not by itself prove that a foreign-key constraint exists. Refer to the actual MySQL constraints when documenting enforced foreign keys.

## 5. Data Types Used

| Data Type | Usage |
|---|---|
| VARCHAR | Identifiers, names, categories, statuses and contact information |
| INT | Integer values and counts |
| BIGINT | Large numeric identifiers |
| DECIMAL | Financial amounts and risk scores |
| DATE | Calendar dates |
| DATETIME | Date and time values |
| TEXT | Descriptions, notes and explanations |
| JSON | Structured old and new audit values |

## 6. Primary Key and Index Information

- Each table has a primary key (`PRI`) as shown in its schema.
- Several relationship and lookup columns have indexes (`MUL`).
- `audit_id`, `issue_id`, and `invoice_record_id` are auto-incrementing primary keys.
- The other primary keys use application-generated identifiers or claim identifiers.

## 7. Data Quality and Fraud Detection Context

ClaimShield uses the database to identify and record suspicious patterns, including:

- Invalid policy references
- Duplicate invoice references
- Payment overstatement
- Shared contact patterns
- Invalid provider relationships

Detected indicators are stored in `fraud_indicators`. Aggregated risk results are stored in `claim_risk_scores`. Investigation activity and evidence are tracked separately to support traceability.

## 8. Documentation Scope

This data dictionary describes the schema retrieved from the `hackathon` MySQL database. Column descriptions are based on their names and their role in the ClaimShield workflow. Where a description represents an inferred business meaning rather than an explicitly defined database constraint, it should be interpreted as documentation guidance.
