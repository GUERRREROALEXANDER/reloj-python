"""Entry point: ``python main.py``."""

import sys


def enable_high_dpi() -> None:
    """Render crisp text on scaled Windows displays."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass


def main() -> None:
    enable_high_dpi()
    from clock_app.ui import ClockApp

    app = ClockApp()
    app.mainloop()


if __name__ == "__main__":
    main()
