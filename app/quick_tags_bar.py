import json
import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMenu, QInputDialog, QMessageBox,
    QDialog, QLineEdit, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QAction

from .i18n import tr
from .logger import debug

COMMANDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "quick_commands.json")


def _load_commands():
    if os.path.exists(COMMANDS_FILE):
        try:
            with open(COMMANDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"groups": []}


def _save_commands(data):
    os.makedirs(os.path.dirname(COMMANDS_FILE), exist_ok=True)
    with open(COMMANDS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class CommandButton(QPushButton):
    context_menu = Signal(int, QPoint)

    def __init__(self, name, command, color, cmd_idx=0):
        super().__init__()
        self._name = name
        self.command = command
        self._color = color
        self._cmd_idx = cmd_idx
        self.setText(name)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(command)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: #252639; color: #cdd6f4;
                border: 1px solid #45475a;
                border-left: 3px solid {color};
                border-radius: 4px;
                padding: 0 14px 0 12px;
                font-size: 10px; font-weight: bold;
            }}
            QPushButton:hover {{ border-color: #89b4fa; }}
        """)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.context_menu.emit(self._cmd_idx, self.mapToGlobal(pos)))
        f = QFont("Segoe UI", 10, QFont.Bold)
        self.setFont(f)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)


class QuickTagsBar(QFrame):
    command_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setStyleSheet("""
            QFrame {
                background-color: #11111b;
                border-top: 1px solid #313244;
            }
        """)

        self._data = _load_commands()
        self._group_idx = 0
        self._cmd_buttons = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)

        self._group_btn = QPushButton()
        self._group_btn.setCursor(Qt.PointingHandCursor)
        self._group_btn.setStyleSheet("""
            QPushButton {
                background-color: #252639; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 0 12px; font-size: 10px; font-weight: bold;
            }
            QPushButton:hover { border-color: #89b4fa; }
        """)
        self._group_btn.clicked.connect(self._on_group_click)
        self._group_btn.setContextMenuPolicy(Qt.CustomContextMenu)
        self._group_btn.customContextMenuRequested.connect(self._on_menu)
        layout.addWidget(self._group_btn)

        sep = QFrame()
        sep.setFixedWidth(1)
        sep.setStyleSheet("background: #313244; margin: 4px 0;")
        layout.addWidget(sep)

        self._cmd_layout = QHBoxLayout()
        self._cmd_layout.setContentsMargins(0, 0, 0, 0)
        self._cmd_layout.setSpacing(4)
        self._cmd_layout.addStretch()
        layout.addLayout(self._cmd_layout, 1)

        self._refresh_ui()

    def _refresh_ui(self):
        debug("QuickTagsBar._refresh_ui")
        for b in self._cmd_buttons:
            self._cmd_layout.removeWidget(b)
            b.deleteLater()
        self._cmd_buttons.clear()

        groups = self._data.get("groups", [])
        if not groups:
            self._group_btn.setText("[No Groups]")
            self._group_btn.setEnabled(False)
            return

        self._group_btn.setEnabled(True)
        if self._group_idx >= len(groups):
            self._group_idx = 0

        g = groups[self._group_idx]
        self._group_btn.setText(g["name"] + "  \u25be")

        color = g.get("color", "#6c7086")
        stretch_idx = self._cmd_layout.count() - 1
        for ci, cmd in enumerate(g.get("commands", [])):
            btn = CommandButton(cmd["name"], cmd["command"], color, ci)
            btn.clicked.connect(lambda checked, c=cmd["command"]: self.command_clicked.emit(c))
            btn.context_menu.connect(lambda ci, pos: self._on_cmd_context(ci, pos))
            self._cmd_layout.insertWidget(stretch_idx, btn)
            self._cmd_buttons.append(btn)

    def _on_cmd_context(self, ci, pos):
        debug("QuickTagsBar._on_cmd_context", ci, pos)
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        edit_a = menu.addAction(tr("quick.edit_command"))
        edit_a.triggered.connect(lambda: self._edit_command(ci))
        del_a = menu.addAction(tr("quick.delete_command"))
        del_a.triggered.connect(lambda: self._delete_command(ci))
        menu.exec(pos)

    def _edit_command(self, ci):
        debug("QuickTagsBar._edit_command", ci)
        groups = self._data.get("groups", [])
        if self._group_idx >= len(groups):
            return
        cmds = groups[self._group_idx].get("commands", [])
        if ci >= len(cmds):
            return
        old = cmds[ci]
        from PySide6.QtWidgets import QInputDialog
        name, ok1 = QInputDialog.getText(self, tr("quick.edit_command"), tr("dialog.name"), text=old["name"])
        if not ok1 or not name.strip():
            return
        cmd, ok2 = QInputDialog.getText(self, tr("quick.edit_command"), tr("dialog.command_to_send"), text=old["command"])
        if not ok2 or not cmd.strip():
            return
        cmds[ci] = {"name": name.strip(), "command": cmd.strip()}
        _save_commands(self._data)
        self._refresh_ui()

    def _delete_command(self, ci):
        debug("QuickTagsBar._delete_command", ci)
        groups = self._data.get("groups", [])
        if self._group_idx >= len(groups):
            return
        cmds = groups[self._group_idx].get("commands", [])
        if ci >= len(cmds):
            return
        r = QMessageBox.question(self, tr("quick.delete_command"),
            tr("quick.delete_confirm").format(cmds[ci]['name']), QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            cmds.pop(ci)
            _save_commands(self._data)
            self._refresh_ui()

    def _on_group_click(self):
        debug("QuickTagsBar._on_group_click")
        groups = self._data.get("groups", [])
        if not groups:
            self._on_menu(None)
            return
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        for i, g in enumerate(groups):
            a = menu.addAction(g["name"])
            if i == self._group_idx:
                a.setEnabled(False)
            else:
                a.triggered.connect(lambda checked, idx=i: self._switch_group(idx))
        menu.addSeparator()
        mgmt =         menu.addAction(tr("quick.manage_groups"))
        mgmt.triggered.connect(lambda: self._on_menu(None))
        menu.exec(self._group_btn.mapToGlobal(
            self._group_btn.rect().bottomLeft()))

    def _on_menu(self, pos):
        debug("QuickTagsBar._on_menu", pos)
        groups = self._data.get("groups", [])
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())

        add_cmd = menu.addAction(tr("quick.add_command"))
        add_cmd.triggered.connect(self._on_add_command)
        menu.addSeparator()

        add_group = menu.addAction(tr("quick.new_group"))
        add_group.triggered.connect(self._on_add_group)

        if groups and self._group_idx < len(groups):
            rename = menu.addAction(tr("quick.rename_group"))
            rename.triggered.connect(self._on_rename_group)
            delete = menu.addAction(tr("quick.delete_group"))
            delete.triggered.connect(self._on_delete_group)

        if groups:
            menu.addSeparator()
            reset = menu.addAction(tr("quick.clear_all"))
            reset.triggered.connect(self._on_reset)

        if pos is not None:
            menu.exec(self._group_btn.mapToGlobal(pos))
        else:
            menu.exec(self._group_btn.mapToGlobal(
                self._group_btn.rect().bottomLeft()))

    def _switch_group(self, idx):
        debug("QuickTagsBar._switch_group", idx)
        self._group_idx = idx
        self._refresh_ui()

    def _on_add_group(self):
        debug("QuickTagsBar._on_add_group")
        name, ok = QInputDialog.getText(self, tr("quick.new_group"), tr("dialog.name"))
        if ok and name.strip():
            groups = self._data.setdefault("groups", [])
            groups.append({"name": name.strip(), "color": "#6c7086", "commands": []})
            self._group_idx = len(groups) - 1
            _save_commands(self._data)
            self._refresh_ui()

    def _on_add_command(self):
        debug("QuickTagsBar._on_add_command")
        groups = self._data.get("groups", [])
        if not groups:
            QMessageBox.information(self, tr("quick.no_group"), tr("quick.create_group_first"))
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(tr("quick.add_command"))
        dlg.setFixedSize(400, 200)
        dlg.setStyleSheet("""
            QDialog { background: #1e1e2e; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px; }
            QLabel { color: #a6adc8; font-size: 12px; }
            QLineEdit { background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px; padding: 8px 10px;
                font-size: 13px; font-family: Consolas, monospace; }
            QPushButton { background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px; padding: 6px 20px; }
            QPushButton:hover { background: #45475a; }
            QPushButton#accent { background: #89b4fa; color: #1e1e2e; font-weight: bold; border: none; }
        """)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        lbl1 = QLabel(tr("dialog.name"))
        layout.addWidget(lbl1)
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Quick Status")
        layout.addWidget(name_edit)

        lbl2 = QLabel(tr("dialog.command_to_send"))
        layout.addWidget(lbl2)
        cmd_edit = QLineEdit()
        cmd_edit.setPlaceholderText("e.g. git status --short")
        layout.addWidget(cmd_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton(tr("dialog.cancel"))
        cancel_btn.clicked.connect(dlg.reject)
        ok_btn = QPushButton(tr("dialog.ok"))
        ok_btn.setObjectName("accent")
        ok_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)
        layout.addLayout(btn_row)

        if dlg.exec() and name_edit.text().strip() and cmd_edit.text().strip():
            groups[self._group_idx]["commands"].append({
                "name": name_edit.text().strip(),
                "command": cmd_edit.text().strip()
            })
            _save_commands(self._data)
            self._refresh_ui()

    def _on_rename_group(self):
        debug("QuickTagsBar._on_rename_group")
        groups = self._data.get("groups", [])
        if not groups or self._group_idx >= len(groups):
            return
        old = groups[self._group_idx]["name"]
        name, ok = QInputDialog.getText(self, tr("quick.rename_group"), "New name:", text=old)
        if ok and name.strip():
            groups[self._group_idx]["name"] = name.strip()
            _save_commands(self._data)
            self._refresh_ui()

    def _on_delete_group(self):
        debug("QuickTagsBar._on_delete_group")
        groups = self._data.get("groups", [])
        if not groups or self._group_idx >= len(groups):
            return
        name = groups[self._group_idx]["name"]
        r = QMessageBox.question(self, tr("quick.delete_group"),
            tr("quick.remove_all"),
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            groups.pop(self._group_idx)
            if self._group_idx >= len(groups):
                self._group_idx = max(0, len(groups) - 1)
            _save_commands(self._data)
            self._refresh_ui()

    def _on_reset(self):
        debug("QuickTagsBar._on_reset")
        r = QMessageBox.question(self, tr("quick.clear_all"),
            tr("quick.remove_all"),
            QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            self._data = {"groups": []}
            _save_commands(self._data)
            self._group_idx = 0
            self._refresh_ui()

    def _menu_style(self):
        return """
            QMenu { background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px; padding: 4px;
                font-size: 12px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #45475a; }
            QMenu::item:disabled { color: #585b70; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 8px; }
        """

    def update_strings(self):
        debug("QuickTagsBar.update_strings")
        pass
