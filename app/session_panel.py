import json
import os

from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTreeWidget, QTreeWidgetItem, QPushButton, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QMenu
)
from PySide2.QtCore import Qt, Signal, QPoint
from PySide2.QtGui import QColor, QFont, QIcon, QPainter, QBrush, QPen
from .i18n import tr
from .logger import debug
from .resources import get_data_dir

HISTORY_FILE = os.path.join(get_data_dir(), "history.json")
MAX_HISTORY = 200

COLOR_TAGS = {
    "ssh": QColor("#a6e3a1"),
    "serial": QColor("#f9e2af"),
    "telnet": QColor("#89b4fa"),
    "local": QColor("#f5c2e7"),
    "default": QColor("#6c7086"),
}


def _color_tag(conn_type):
    return COLOR_TAGS.get(conn_type, COLOR_TAGS["default"])


class SessionTreeItem(QWidget):
    def __init__(self, name, conn_type="ssh", status="connected"):
        super().__init__()
        self.name = name
        self.conn_type = conn_type
        self.status = status
        self.setMinimumHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 8, 4)
        layout.setSpacing(6)

        dot = QLabel("\u25cf")
        c = _color_tag(conn_type)
        if status == "disconnected":
            c = QColor("#585b70")
        elif status == "saved":
            c = QColor("#6c7086")
        dot.setStyleSheet(f"color: {c.name()}; font-size: 10px; background: transparent;")
        dot.setFixedWidth(14)
        layout.addWidget(dot)

        lbl = QLabel(name)
        lbl.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; padding: 1px 0;")
        lbl.setAlignment(Qt.AlignVCenter)
        self.name_label = lbl
        layout.addWidget(lbl, 1)

        if status == "saved":
            self.status_label = QLabel("\u25c1")
            self.status_label.setStyleSheet("color: #6c7086; font-size: 10px; background: transparent;")
        else:
            self.status_label = QLabel("\u25b6" if status == "connected" else "\u25a0")
            self.status_label.setStyleSheet(
                f"color: {'#a6e3a1' if status == 'connected' else '#f38ba8'}; font-size: 10px; background: transparent;")
        layout.addWidget(self.status_label)

    def update_status(self, status):
        self.status = status
        c = _color_tag(self.conn_type)
        if status == "disconnected":
            c = QColor("#585b70")
            self.status_label.setText("\u25a0")
            self.status_label.setStyleSheet("color: #f38ba8; font-size: 10px; background: transparent;")
        elif status == "saved":
            c = QColor("#6c7086")
            self.status_label.setText("\u25c1")
            self.status_label.setStyleSheet("color: #6c7086; font-size: 10px; background: transparent;")
        else:
            self.status_label.setText("\u25b6")
            self.status_label.setStyleSheet("color: #a6e3a1; font-size: 10px; background: transparent;")
        dot = self.findChild(QLabel)
        if dot:
            dot.setStyleSheet(f"color: {c.name()}; font-size: 10px; background: transparent;")


class SessionTreePanel(QWidget):
    session_selected = Signal(int)
    saved_session_clicked = Signal(str)
    session_context_menu = Signal(int, QPoint)
    edit_saved = Signal(str, QPoint)
    active_dbl_click = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._saved_items = []
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 8, 12, 4)

        self._session_title = QLabel(tr("session_panel.title"))
        self._session_title.setStyleSheet("color: #89b4fa; font-size: 12px; font-weight: bold; background: transparent;")
        hl.addWidget(self._session_title)
        hl.addStretch()

        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("color: #585b70; font-size: 11px; background: transparent;")
        hl.addWidget(self.count_label)
        layout.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #313244; margin: 0 8px;")
        layout.addWidget(sep)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("\U0001f50d " + tr("session_panel.filter"))
        self.filter_input.setStyleSheet("""
            QLineEdit {
                background-color: #252639; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                padding: 6px 10px; font-size: 12px;
                margin: 4px 8px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self.filter_input.textChanged.connect(self._on_filter)
        layout.addWidget(self.filter_input)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                border: none;
                padding: 2px 0;
            }
            QListWidget::item:hover {
                background-color: #252639;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #313244;
                border-radius: 6px;
            }
        """)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._on_list_context)
        layout.addWidget(self.list_widget, 1)

    def add_session(self, name, conn_type="ssh", status="connected"):
        debug(f"SessionPanel.add_session name={name} type={conn_type} status={status}")
        item = QListWidgetItem()
        widget = SessionTreeItem(name, conn_type, status)
        item.setSizeHint(widget.minimumSizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self._items.append((name, conn_type, status, item))
        self._update_count()
        return len(self._items) - 1

    def add_saved_session(self, name, conn_type="ssh"):
        item = QListWidgetItem()
        widget = SessionTreeItem(name, conn_type, "saved")
        item.setSizeHint(widget.minimumSizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)
        self._saved_items.append((name, conn_type, item))
        self._update_count()

    def find_session(self, name):
        for idx, (sname, _, _, _) in enumerate(self._items):
            if sname == name:
                return idx
        return -1

    def activate_saved(self, name, conn_type="ssh"):
        debug(f"SessionPanel.activate_saved name={name} type={conn_type}")
        for i, (sname, stype, sitem) in enumerate(self._saved_items):
            if sname == name:
                self._saved_items.pop(i)
                widget = self.list_widget.itemWidget(sitem)
                if widget:
                    widget.update_status("connected")
                self._items.append((name, conn_type, "connected", sitem))
                idx = len(self._items) - 1
                self._update_count()
                return idx
        return self.add_session(name, conn_type, "connected")

    def deactivate_to_saved(self, idx, saved_name=None):
        debug(f"SessionPanel.deactivate_to_saved idx={idx} saved_name={saved_name}")
        if 0 <= idx < len(self._items):
            _, _, _, item = self._items.pop(idx)
            widget = self.list_widget.itemWidget(item)
            name = saved_name or (widget.name_label.text() if (widget and hasattr(widget, 'name_label')) else "")
            conn_type = widget.conn_type if widget else "ssh"
            if widget:
                widget.update_status("saved")
            self._saved_items.append((name, conn_type, item))
            self._update_count()

    def _update_count(self):
        self.count_label.setText(f"{len(self._items)}+{len(self._saved_items)}")

    def update_session(self, idx, name=None, status=None):
        if 0 <= idx < len(self._items):
            _, conn_type, old_status, item = self._items[idx]
            if name:
                self._items[idx] = (name, conn_type, status or old_status, item)
            if status:
                self._items[idx] = (self._items[idx][0], conn_type, status, item)
            widget = self.list_widget.itemWidget(item)
            if widget and status:
                widget.update_status(status)
            if widget and name:
                widget.name = name

    def remove_session(self, idx):
        if 0 <= idx < len(self._items):
            _, _, _, item = self._items[idx]
            self.list_widget.takeItem(self.list_widget.row(item))
            self._items.pop(idx)
            self._update_count()

    def remove_saved(self, name):
        for i, (sname, _, sitem) in enumerate(self._saved_items):
            if sname == name:
                self._saved_items.pop(i)
                row = self.list_widget.row(sitem)
                if row >= 0:
                    self.list_widget.takeItem(row)
                self._update_count()
                return

    def clear_all(self):
        self.list_widget.clear()
        self._items.clear()
        self._saved_items.clear()
        self._update_count()

    def _on_filter(self, text):
        for name, _, _, item in self._items:
            row = self.list_widget.row(item)
            it = self.list_widget.item(row)
            if it:
                it.setHidden(text.lower() not in name.lower() if text else False)
        for name, _, item in self._saved_items:
            row = self.list_widget.row(item)
            it = self.list_widget.item(row)
            if it:
                it.setHidden(text.lower() not in name.lower() if text else False)

    def _on_item_clicked(self, item):
        for idx, (name, _, _, it) in enumerate(self._items):
            if it is item:
                self.session_selected.emit(idx)
                return

    def _on_item_double_clicked(self, item):
        for name, _, it in self._saved_items:
            if it is item:
                self.saved_session_clicked.emit(name)
                return
        for idx, (_, _, _, it) in enumerate(self._items):
            if it is item:
                self.active_dbl_click.emit(idx)
                return

    def _on_list_context(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        for idx, (name, _, _, it) in enumerate(self._items):
            if it is item:
                self.session_context_menu.emit(idx, self.list_widget.mapToGlobal(pos))
                return
        for name, _, it in self._saved_items:
            if it is item:
                self.edit_saved.emit(name, self.list_widget.mapToGlobal(pos))
                return

    def update_strings(self):
        self._session_title.setText("\u25c6 " + tr("session_panel.title"))
        self.filter_input.setPlaceholderText("\U0001f50d " + tr("session_panel.filter"))


class HistoryPanel(QWidget):
    command_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmds = []
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header = QWidget()
        header.setStyleSheet("background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 4, 12, 2)

        self._history_title = QLabel("\u25c6 " + tr("session_panel.history"))
        title = self._history_title
        title.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold; background: transparent;")
        hl.addWidget(title)
        hl.addStretch()

        self.clear_h = QPushButton("\u2716")
        self.clear_h.setFixedSize(20, 20)
        self.clear_h.setStyleSheet("""
            QPushButton {
                background: transparent; color: #585b70;
                border: none; font-size: 10px;
            }
            QPushButton:hover { color: #f38ba8; }
        """)
        self.clear_h.clicked.connect(self.clear_history)
        hl.addWidget(self.clear_h)

        layout.addWidget(header)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
                font-size: 11px;
                color: #6c7086;
            }
            QListWidget::item {
                padding: 4px 12px;
                border: none;
            }
            QListWidget::item:hover {
                background-color: #252639;
                color: #cdd6f4;
                border-radius: 4px;
            }
        """)
        self.history_list.itemClicked.connect(
            lambda item: self.command_selected.emit(item.text()))
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self._on_history_context)
        layout.addWidget(self.history_list, 1)

        self._load_history()

    def add_command(self, cmd):
        # Remove ALL previous occurrences, then insert at front
        while cmd in self._cmds:
            old_idx = self._cmds.index(cmd)
            self._cmds.pop(old_idx)
            row = self.history_list.count() - 1 - old_idx
            item = self.history_list.takeItem(row)
            if item:
                del item
        self._cmds.append(cmd)
        item = QListWidgetItem(cmd)
        self.history_list.insertItem(0, item)
        if len(self._cmds) > MAX_HISTORY:
            removed = self._cmds.pop(0)
            last_item = self.history_list.item(self.history_list.count() - 1)
            if last_item:
                self.history_list.takeItem(self.history_list.count() - 1)
        self._save_history()

    def record_command(self, cmd):
        """Record command without reordering (used for click-send)."""
        if cmd in self._cmds:
            return
        self._cmds.append(cmd)
        item = QListWidgetItem(cmd)
        self.history_list.insertItem(0, item)
        if len(self._cmds) > MAX_HISTORY:
            self._cmds.pop(0)
            last_item = self.history_list.item(self.history_list.count() - 1)
            if last_item:
                self.history_list.takeItem(self.history_list.count() - 1)
        self._save_history()

    def clear_history(self):
        self._cmds.clear()
        self.history_list.clear()
        self._save_history()

    def _load_history(self):
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    # Deduplicate: keep only the LATEST occurrence of each cmd
                    seen = set()
                    deduped = []
                    for cmd in reversed(data):
                        if cmd not in seen:
                            seen.add(cmd)
                            deduped.append(cmd)
                    deduped.reverse()
                    self._cmds = deduped[-MAX_HISTORY:]
                    for cmd in reversed(self._cmds):
                        item = QListWidgetItem(cmd)
                        self.history_list.addItem(item)
        except Exception:
            self._cmds = []

    def _save_history(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._cmds[-MAX_HISTORY:], f, ensure_ascii=False)
        except Exception:
            pass

    def _on_history_context(self, pos):
        item = self.history_list.itemAt(pos)
        if not item:
            return
        from PySide2.QtWidgets import QApplication
        menu = QMenu(self)
        copy_act = menu.addAction(tr("menu.edit.copy"))
        copy_act.triggered.connect(lambda: QApplication.clipboard().setText(item.text()))
        menu.exec_(self.history_list.mapToGlobal(pos))

    def update_strings(self):
        self._history_title.setText("\u25c6 " + tr("session_panel.history"))
