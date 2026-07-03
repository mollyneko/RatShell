from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QRadioButton, QApplication, QButtonGroup
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from .i18n import tr, set_language, current_language
from .resources import apply_theme, DARK_THEME, LIGHT_THEME
from .logger import debug


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("menu.tools.options"))
        self.setFixedSize(420, 320)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._result = None
        self._parent = parent

        app = QApplication.instance()
        self._current_theme = app.property("theme") or "dark"
        self._current_lang = current_language()

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        container = QWidget()
        container.setObjectName("dialogContainer")
        self._update_container_style(container)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet("background: transparent;")
        tb = QHBoxLayout(title_bar)
        tb.setContentsMargins(16, 0, 8, 0)

        title_label = QLabel("\u2699 " + tr("menu.tools.options"))
        title_label.setStyleSheet("color: #cdd6f4; font-size: 15px; font-weight: bold; background: transparent;")
        tb.addWidget(title_label)
        tb.addStretch()

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6c7086; border: none;
                font-size: 14px; border-radius: 16px;
            }
            QPushButton:hover { background-color: #f38ba8; color: white; }
        """)
        close_btn.clicked.connect(self.reject)
        tb.addWidget(close_btn)

        layout.addWidget(title_bar)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        form = QVBoxLayout(content)
        form.setContentsMargins(24, 12, 24, 24)
        form.setSpacing(16)

        theme_lbl = QLabel(tr("menu.tools.theme"))
        theme_lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold; background: transparent;")
        form.addWidget(theme_lbl)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(16)
        self.theme_group = QButtonGroup(self)
        self.theme_dark = QRadioButton(tr("options.theme_dark"))
        self.theme_dark.setChecked(self._current_theme == "dark")
        self.theme_dark.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; spacing: 6px;")
        self.theme_group.addButton(self.theme_dark)
        theme_row.addWidget(self.theme_dark)
        self.theme_light = QRadioButton(tr("options.theme_light"))
        self.theme_light.setChecked(self._current_theme == "light")
        self.theme_light.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; spacing: 6px;")
        self.theme_group.addButton(self.theme_light)
        theme_row.addWidget(self.theme_light)
        theme_row.addStretch()
        form.addLayout(theme_row)
        self.theme_group.buttonToggled.connect(self._on_theme_changed)

        lang_lbl = QLabel(tr("menu.tools.language"))
        lang_lbl.setStyleSheet("color: #89b4fa; font-size: 13px; font-weight: bold; background: transparent;")
        form.addWidget(lang_lbl)

        lang_row = QHBoxLayout()
        lang_row.setSpacing(16)
        self.lang_group = QButtonGroup(self)
        self.lang_zh = QRadioButton(tr("options.lang_zh"))
        self.lang_zh.setChecked(self._current_lang == "zh")
        self.lang_zh.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; spacing: 6px;")
        self.lang_group.addButton(self.lang_zh)
        lang_row.addWidget(self.lang_zh)
        self.lang_en = QRadioButton(tr("options.lang_en"))
        self.lang_en.setChecked(self._current_lang == "en")
        self.lang_en.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; spacing: 6px;")
        self.lang_group.addButton(self.lang_en)
        lang_row.addWidget(self.lang_en)
        lang_row.addStretch()
        form.addLayout(lang_row)
        self.lang_group.buttonToggled.connect(self._on_lang_changed)

        form.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self.apply_btn = QPushButton(tr("dialog.ok"))
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                padding: 10px 28px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """)
        self.apply_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.apply_btn)

        form.addLayout(btn_row)

        layout.addWidget(content, 1)
        root.addWidget(container)

    def _update_container_style(self, container):
        is_dark = self._current_theme == "dark"
        bg = "#1e1e2e" if is_dark else "#eff1f5"
        border = "#45475a" if is_dark else "#ccd0da"
        container.setStyleSheet(f"""
            QWidget#dialogContainer {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)

    def _on_theme_changed(self, btn, checked):
        if not checked:
            return
        debug("OptionsDialog theme changed")
        app = QApplication.instance()
        new_theme = "dark" if btn == self.theme_dark else "light"
        if new_theme == self._current_theme:
            return
        apply_theme(app, new_theme)
        app.setProperty("theme", new_theme)
        self._current_theme = new_theme
        self._update_container_style(self.findChild(QWidget, "dialogContainer"))
        if self._parent and hasattr(self._parent, '_apply_terminal_theme'):
            self._parent._apply_terminal_theme(new_theme)

    def _on_lang_changed(self, btn, checked):
        if not checked:
            return
        debug("OptionsDialog lang changed")
        new_lang = "zh" if btn == self.lang_zh else "en"
        if new_lang == self._current_lang:
            return
        set_language(new_lang)
        self._current_lang = new_lang
        if self._parent and hasattr(self._parent, '_rebuild_ui_strings'):
            self._parent._rebuild_ui_strings()
