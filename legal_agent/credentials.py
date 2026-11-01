"""Local server credentials; never place these in report settings or UI widgets."""
import json
import os
import tempfile
from pathlib import Path

PKULAW_SECRET_FILE = Path(__file__).resolve().parents[1] / ".streamlit" / "pkulaw.local.json"


def backend_pkulaw_token(path=None):
    token = os.environ.get("PKULAW_TOKEN", "").strip()
    if not token:
        try:
            data = json.loads(Path(path or PKULAW_SECRET_FILE).read_text())
            token = data.get("token", "")
        except (OSError, ValueError, AttributeError):
            return ""
    if not isinstance(token, str):
        return ""
    token = token.strip().removeprefix("Bearer ").strip()
    return token if token and not any(c in token for c in "\r\n") and token.lower() not in {"[redacted]", "<redacted>", "**********"} else ""


def save_backend_pkulaw_token(token, path=None):
    """Called inside the local backend, never by reading browser password values."""
    if not isinstance(token, str) or not token.strip() or any(c in token for c in "\r\n"):
        raise ValueError("invalid_token")
    path = Path(path or PKULAW_SECRET_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".pku-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump({"token": token.strip()}, output)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
