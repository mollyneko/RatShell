import json
import os
from .logger import debug

SESSIONS_DIR = None


def _ensure_dir():
    debug("session_manager._ensure_dir")
    global SESSIONS_DIR
    if SESSIONS_DIR is None:
        SESSIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sessions")
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def _safe_path(name):
    debug("session_manager._safe_path", name)
    safe = "".join(c if c.isalnum() or c in "._- " else "_" for c in name)
    return os.path.join(_ensure_dir() or SESSIONS_DIR, f"{safe}.json")


def list_sessions():
    debug("session_manager.list_sessions")
    _ensure_dir()
    sessions = []
    for f in sorted(os.listdir(SESSIONS_DIR)):
        if f.endswith(".json"):
            try:
                with open(os.path.join(SESSIONS_DIR, f), "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                sessions.append((f[:-5], data))
            except Exception:
                continue
    return sessions


def save_session(name, data):
    debug("session_manager.save_session", name)
    path = _safe_path(name)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)


def load_session(name):
    debug("session_manager.load_session", name)
    path = _safe_path(name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    return None


def delete_session(name):
    debug("session_manager.delete_session", name)
    path = _safe_path(name)
    if os.path.exists(path):
        os.remove(path)


def default_session_data(conn_type="ssh"):
    debug("session_manager.default_session_data", conn_type)
    base = {
        "type": conn_type,
        "host": "",
        "port": 22,
        "username": "",
        "password": "",
        "timeout": 30,
        "color_scheme": "dark",
    }
    if conn_type == "serial":
        base.update({"port": "COM1", "baudrate": 115200, "bytesize": 8, "parity": "N", "stopbits": 1})
    elif conn_type == "telnet":
        base["port"] = 23
    return base
