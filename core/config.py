"""Settings persistence under the user's home directory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".offline-video-converter"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    _ensure_dir()
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(data: dict[str, Any]) -> None:
    _ensure_dir()
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_feature_settings(feature: str) -> dict[str, Any]:
    config = load_config()
    return dict(config.get("features", {}).get(feature, {}))


def save_feature_settings(feature: str, settings: dict[str, Any]) -> None:
    config = load_config()
    features = config.setdefault("features", {})
    features[feature] = settings
    save_config(config)


def append_history(entry: dict[str, Any], max_entries: int = 50) -> None:
    _ensure_dir()
    history: list[dict[str, Any]] = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            history = []
    history.insert(0, entry)
    history = history[:max_entries]
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


def pop_last_history() -> dict[str, Any] | None:
    _ensure_dir()
    if not HISTORY_FILE.exists():
        return None
    try:
        history: list[dict[str, Any]] = json.loads(
            HISTORY_FILE.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return None
    if not history:
        return None
    last = history.pop(0)
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return last
