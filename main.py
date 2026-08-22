"""Entry point - GUI when no args, CLI when args are passed."""

from __future__ import annotations

import sys


def main() -> int:
    if len(sys.argv) > 1:
        from cli import main as cli_main

        return cli_main(sys.argv[1:])
    from gui.main_window import run_gui

    return run_gui()


if __name__ == "__main__":
    sys.exit(main())
