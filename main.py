"""Entry point - GUI when no args, CLI when args are passed."""

from __future__ import annotations

import os
import sys


def _configure_qt() -> None:
    """Configure Qt before any PySide6 modules are imported."""
    rules = [r.strip() for r in os.environ.get("QT_LOGGING_RULES", "").split(";") if r.strip()]
    for rule in ("qt.qpa.window=false", "qt.multimedia.ffmpeg=false"):
        prefix = rule.split("=", 1)[0]
        if not any(r.startswith(f"{prefix}=") for r in rules):
            rules.append(rule)
    os.environ["QT_LOGGING_RULES"] = ";".join(rules)

    if sys.platform == "win32":
        import ctypes

        try:
            # Match Qt 6 default so it does not retry and log "Access is denied".
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass


def main() -> int:
    if len(sys.argv) > 1:
        from cli import main as cli_main

        return cli_main(sys.argv[1:])
    _configure_qt()
    from gui.main_window import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
