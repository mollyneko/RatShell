#!/usr/bin/env python3
"""
Frtty Pro v1.0
A modern SSH / Serial / Telnet terminal emulator.
Built with PySide2 — inspired by frtty (PuTTY fork).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from PySide2.QtGui import QFont, QIcon

from app.main_window import MainWindow
from app.resources import apply_theme, APP_NAME, APP_VERSION, get_app_dir


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("RatStudio")
    icon_path = os.path.join(get_app_dir(), "frtty.png")
    app.setWindowIcon(QIcon(icon_path))
    apply_theme(app)

    window = MainWindow()
    window.setWindowIcon(QIcon(icon_path))
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
