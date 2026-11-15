
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME", "hackathon"),
}

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 20261115

TOTAL_CLAIMANTS = 2000
TOTAL_POLICIES = 2000
TOTAL_CLAIMS = 5000
TOTAL_INCIDENTS = 5000
TOTAL_PROVIDERS = 500
TOTAL_RELATIONSHIP_EDGES = 8000
