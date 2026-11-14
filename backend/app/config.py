from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILENAME = "saldoclaro.db"
DATABASE_URL = f"sqlite:///{BACKEND_DIR / DATABASE_FILENAME}"

APP_NAME = "SaldoClaro"
APP_DESCRIPTION = "API REST para organização financeira pessoal."
APP_VERSION = "0.1.0"
