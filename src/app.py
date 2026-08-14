# Katip Celebi
# Copyright (C) 2026 farukylmz0550
"""Entrypoint wrapper that launches the UI in `app_shell`.

This file is intentionally small: the heavy UI logic lives in
`app_shell.py` so that PyInstaller analysis stays focused.
"""

import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from shared import config, texts
from shared.theme import apply_theme
from app_shell import MainWindow


def main() -> int:
    # High-DPI rounding policy so scaled displays render crisply.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("KatipCelebi")
    texts.use(config.language())
    apply_theme(app, config.theme())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())


def main() -> int:
    # Before the QApplication: at 125% or 150% Qt otherwise rounds the scale to
    # a whole number, so the whole window is laid out for 100% or 200% and then
    # stretched to fit. PassThrough follows the display exactly.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("KatipCelebi")
    # Before any widget is built: they read their labels as they are made.
    texts.use(config.language())
    apply_theme(app, config.theme())

    if sys.platform == "win32":
        # Windows groups taskbar buttons by this id; without it the app appears
        # under Python's icon rather than its own.
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "farukylmz0550.KatipCelebi"
            )
        except Exception:
            logger.debug("Could not claim a taskbar identity", exc_info=True)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
