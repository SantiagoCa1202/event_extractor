import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    load_dotenv = None


def _load_env_files() -> str:
    project_root = Path(__file__).resolve().parent
    default_env = project_root / ".env"
    if load_dotenv and default_env.exists():
        load_dotenv(default_env, override=False)

    app_env = os.getenv("APP_ENV", "dev").strip().lower() or "dev"
    env_file = project_root / f".env.{app_env}"
    if load_dotenv and env_file.exists():
        load_dotenv(env_file, override=False)
    return app_env


APP_ENV = _load_env_files()
DEFAULT_TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD = os.getenv("TESSERACT_CMD", DEFAULT_TESSERACT_CMD)
OPS_EVENTS_API_BASE_URL = os.getenv("OPS_EVENTS_API_BASE_URL", "").strip()
OPS_EVENTS_API_TOKEN = os.getenv("OPS_EVENTS_API_TOKEN", "").strip()
OPS_EVENTS_API_ENABLED = os.getenv("OPS_EVENTS_API_ENABLED", "true").strip()
OPS_EVENTS_API_TIMEOUT_SECONDS = os.getenv("OPS_EVENTS_API_TIMEOUT_SECONDS", "30").strip()
DEFAULT_EVENT_FUNCTIONS_SCOPE = "food_only"
EVENT_FUNCTIONS_SCOPE = os.getenv("EVENT_FUNCTIONS_SCOPE", DEFAULT_EVENT_FUNCTIONS_SCOPE).strip().lower()


def get_event_functions_scope() -> str:
    value = os.getenv("EVENT_FUNCTIONS_SCOPE", EVENT_FUNCTIONS_SCOPE).strip().lower()
    if value in {"all", "all_functions", "everything"}:
        return "all"
    return DEFAULT_EVENT_FUNCTIONS_SCOPE


def include_all_event_functions() -> bool:
    return get_event_functions_scope() == "all"
