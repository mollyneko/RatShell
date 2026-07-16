APP_NAME = "Frtty Pro"
APP_VERSION = "1.3.0"
ORG_NAME = "RatStudio"

import os


def get_data_dir():
    """Return a persistent user data directory (not temp frozen dir)."""
    base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    d = os.path.join(base, ORG_NAME, APP_NAME.replace(" ", ""))
    os.makedirs(d, exist_ok=True)
    return d


def get_app_dir():
    """Return the directory where app data files (icons, etc.) are stored.
    Works both in development and PyInstaller frozen mode."""
    import sys
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DARK_THEME = """
QWidget {
    background-color: #1a1b2e;
    color: #cdd6f4;
    font-family: "Cascadia Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 13px;
}
QMainWindow { background-color: #1a1b2e; }
QLabel { color: #cdd6f4; background: transparent; }
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
}
QPushButton:hover {
    background-color: #45475a;
    border-color: #585b70;
}
QPushButton:pressed {
    background-color: #585b70;
}
QPushButton#accentBtn {
    background-color: #89b4fa;
    color: #1e1e2e;
    font-weight: bold;
    border: none;
}
QPushButton#accentBtn:hover {
    background-color: #74c7ec;
}
QPushButton#dangerBtn {
    background-color: #f38ba8;
    color: #1e1e2e;
    border: none;
}
QPushButton#dangerBtn:hover {
    background-color: #eba0ac;
}
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: #89b4fa;
    selection-color: #1e1e2e;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
    border-color: #89b4fa;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
}
QComboBox:hover { border-color: #585b70; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #cdd6f4;
    margin-right: 6px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
}
QTabWidget::pane {
    background-color: #1a1b2e;
    border: none;
    border-top: 1px solid #313244;
}
QTabBar::tab {
    background-color: #1a1b2e;
    color: #6c7086;
    border: none;
    border-bottom: 2px solid transparent;
    padding: 8px 16px;
    min-width: 80px;
}
QTabBar::tab:hover {
    color: #cdd6f4;
    background-color: #252639;
}
QTabBar::tab:selected {
    color: #89b4fa;
    border-bottom: 2px solid #89b4fa;
    background-color: #252639;
}
QScrollBar:vertical {
    background: #1a1b2e;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1a1b2e;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QMenu {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #45475a;
}
QMenu::separator {
    height: 1px;
    background: #45475a;
    margin: 4px 8px;
}
QCheckBox {
    spacing: 8px;
    color: #cdd6f4;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #585b70;
    background-color: #313244;
}
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #89b4fa;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QSplitter::handle {
    background: #45475a;
    width: 1px;
}
QDockWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: none;
    titlebar-close-icon: none;
}
QDockWidget::title {
    background-color: #181825;
    padding: 4px 8px;
    font-size: 11px;
    border-bottom: 1px solid #313244;
}
QRadioButton {
    color: #a6adc8;
    font-size: 11px;
    spacing: 4px;
    background: transparent;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid #585b70;
    background-color: #313244;
}
QRadioButton::indicator:checked {
    background-color: #89b4fa;
    border-color: #89b4fa;
}
QSpinBox, QDoubleSpinBox {
    background: #252639;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 2px 4px;
    font-size: 11px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #89b4fa;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    border-left: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
    border-top-right-radius: 4px;
    background: #313244;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    border-left: 1px solid #45475a;
    border-bottom-right-radius: 4px;
    background: #313244;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #cdd6f4;
    margin-top: 2px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #cdd6f4;
    margin-bottom: 2px;
}
QListWidget {
    background-color: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 2px 8px;
    border: none;
}
QListWidget::item:hover {
    background-color: #252639;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #313244;
    border-radius: 4px;
}
"""

def apply_theme(app):
    app.setStyleSheet(DARK_THEME)
