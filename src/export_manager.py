
import csv
import json
import os
import subprocess
from pathlib import Path

from config import DB_CONFIG
from src.storage import get_connection


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPORT_ROOT = PROJECT_ROOT / "exports"

CSV_DIR = EXPORT_ROOT / "csv"
JSON_DIR = EXPORT_ROOT / "json"
SQL_DIR = EXPORT_ROOT / "sql"

MANIFEST_PATH = EXPORT_ROOT / "export_manifest.json"

MYSQLDUMP_PATH = Path(
    r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe"
)


# --------------------------------------------------
# DATABASE TABLES
# --------------------------------------------------

TABLES = [
    "claimants",
    "policies",
    "incidents",
    "providers",
    "claims",
    "invoices",
    "payments",
    "relationship_edges",
    "fraud_indicators",
    "claim_risk_scores",
    "investigations",
    "investigation_events",
    "audit_logs",
    "data_quality_issues",
    "investigation_evidence",
]


# --------------------------------------------------
# CREATE EXPORT DIRECTORIES
# --------------------------------------------------

def create_export_directories():
    for directory in [CSV_DIR, JSON_DIR, SQL_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# EXPORT ONE TABLE TO CSV AND JSON
# --------------------------------------------------

def export_table(cursor, table_name):
    print(f"\nExporting table: {table_name}")

    cursor.execute(f"SELECT * FROM `{table_name}`")

    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    records = [
        dict(zip(columns, row))
        for row in rows
    ]

    # CSV EXPORT
    csv_path = CSV_DIR / f"{table_name}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)

    # JSON EXPORT
    json_path = JSON_DIR / f"{table_name}.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(
            records,
            file,
            indent=4,
            default=str,
            ensure_ascii=False
        )

    print(f"  Database rows : {len(records)}")
    print(f"  CSV created   : {csv_path.name}")
    print(f"  JSON created  : {json_path.name}")

    return {
        "table": table_name,
        "database_rows": len(records),
        "csv_path": str(csv_path.relative_to(PROJECT_ROOT)),
        "json_path": str(json_path.relative_to(PROJECT_ROOT)),
    }


# --------------------------------------------------
# VERIFY CSV AND JSON EXPORTS
# --------------------------------------------------

def verify_exports(manifest):
    print("\n" + "=" * 60)
    print("EXPORT VERIFICATION")
    print("=" * 60)

    for item in manifest:
        csv_path = PROJECT_ROOT / item["csv_path"]
        json_path = PROJECT_ROOT / item["json_path"]

        # Verify CSV row count
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as file:
            csv_count = sum(1 for _ in csv.DictReader(file))

        # Verify JSON row count
        with open(json_path, "r", encoding="utf-8") as file:
            json_records = json.load(file)

        json_count = len(json_records)
        database_count = item["database_rows"]

        passed = (
            database_count == csv_count == json_count
        )

        item["csv_rows"] = csv_count
        item["json_rows"] = json_count
        item["verification"] = "PASS" if passed else "FAIL"

        print(
            f"{item['table']:<25} "
            f"DB: {database_count:<7} "
            f"CSV: {csv_count:<7} "
            f"JSON: {json_count:<7} "
            f"{item['verification']}"
        )

    return all(
        item["verification"] == "PASS"
        for item in manifest
    )


# --------------------------------------------------
# CREATE MYSQL SQL BACKUP
# --------------------------------------------------

def create_sql_backup():
    print("\nCreating MySQL SQL backup...")

    if not MYSQLDUMP_PATH.exists():
        raise FileNotFoundError(
            f"mysqldump.exe not found at: {MYSQLDUMP_PATH}"
        )

    database_name = DB_CONFIG.get("database")

    if not database_name:
        raise ValueError(
            "Database name is missing from DB_CONFIG."
        )

    sql_path = SQL_DIR / f"{database_name}_backup.sql"

    command = [
        str(MYSQLDUMP_PATH),
        f"--host={DB_CONFIG['host']}",
        f"--port={DB_CONFIG['port']}",
        f"--user={DB_CONFIG['user']}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--databases",
        database_name,
    ]

    # Pass the password through the child process environment,
    # not as a command-line argument.
    process_env = os.environ.copy()

    password = DB_CONFIG.get("password")
    if password:
        process_env["MYSQL_PWD"] = str(password)

    with open(sql_path, "wb") as output_file:
        result = subprocess.run(
            command,
            stdout=output_file,
            stderr=subprocess.PIPE,
            env=process_env,
            check=False,
        )

    if result.returncode != 0:
        error_message = result.stderr.decode(
            "utf-8", errors="replace"
        )
        raise RuntimeError(
            f"MySQL backup failed:\n{error_message}"
        )

    if not sql_path.exists() or sql_path.stat().st_size == 0:
        raise RuntimeError("SQL backup file is empty or missing.")

    print(f"SQL backup created: {sql_path}")
    print(f"Backup size: {sql_path.stat().st_size:,} bytes")

    return sql_path


# --------------------------------------------------
# SAVE EXPORT MANIFEST
# --------------------------------------------------

def save_manifest(manifest, sql_path, verification_passed):
    output = {
        "database": DB_CONFIG.get("database"),
        "total_tables": len(manifest),
        "verification": (
            "PASS" if verification_passed else "FAIL"
        ),
        "sql_backup": str(sql_path.relative_to(PROJECT_ROOT)),
        "tables": manifest,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=4)

    print(f"\nExport manifest saved: {MANIFEST_PATH}")


# --------------------------------------------------
# MAIN EXPORT WORKFLOW
# --------------------------------------------------

def run_exports():
    print("=" * 60)
    print("CLAIMSHIELD - DATA EXPORT AND REPRODUCIBILITY")
    print("=" * 60)

    create_export_directories()

    connection = None
    manifest = []

    try:
        connection = get_connection()
        cursor = connection.cursor()

        for table_name in TABLES:
            result = export_table(cursor, table_name)
            manifest.append(result)

        cursor.close()

    finally:
        if connection is not None and connection.is_connected():
            connection.close()

    verification_passed = verify_exports(manifest)

    sql_path = create_sql_backup()

    save_manifest(
        manifest,
        sql_path,
        verification_passed
    )

    print("\n" + "=" * 60)
    print("EXPORT WORKFLOW SUMMARY")
    print("=" * 60)

    print(f"Tables exported : {len(manifest)}")
    print(f"CSV directory   : {CSV_DIR}")
    print(f"JSON directory  : {JSON_DIR}")
    print(f"SQL backup      : {sql_path.name}")
    print(
        "Verification    : "
        + ("PASS" if verification_passed else "FAIL")
    )

    if not verification_passed:
        raise RuntimeError(
            "Export verification failed. Check the row counts above."
        )

    print("\nClaimShield data export completed successfully.")


if __name__ == "__main__":
    run_exports()
