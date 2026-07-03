#!/usr/bin/env python3
"""
RatShell v1.0
A modern SSH / Serial / Telnet terminal emulator.
Built with PySide6 — inspired by frtty (PuTTY fork).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from app.main_window import MainWindow
from app.resources import apply_theme, APP_NAME, APP_VERSION


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("RatStudio")
    app.setProperty("theme", "dark")

    apply_theme(app, "dark")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
