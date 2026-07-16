import json
import os

from PySide2.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QPushButton, QLabel, QLineEdit, QMenu, QMenuBar, QSplitter,
    QFrame, QSizePolicy, QApplication, QDockWidget, QListWidget,
    QMessageBox, QDialog, QAction
)
from PySide2.QtCore import Qt, Signal, Slot, QTimer, QSize, QPoint
from PySide2.QtGui import QFont, QColor, QPalette, QIcon, QPainter, QBrush, QPen

from .title_bar import TitleBar
from .terminal_widget import TerminalWidget
from .connection_dialog import ConnectionDialog
from .logger import debug
from .send_panel import SendPanel
from .session_panel import SessionTreePanel, HistoryPanel
from .quick_tags_bar import QuickTagsBar
from .connections import create_connection
from .session_manager import list_sessions, load_session, save_session, delete_session
from .resources import APP_NAME, APP_VERSION, get_data_dir, get_app_dir
from .i18n import tr

TAB_COLORS = {
    "ssh": "#a6e3a1",
    "serial": "#f9e2af",
    "telnet": "#89b4fa",
    "local": "#f5c2e7",
    "default": "#6c7086",
}


class ColorTabButton(QPushButton):
    context_menu = Signal(int, QPoint)
    close_clicked = Signal(int)

    def __init__(self, label, conn_type="ssh", idx=0, parent=None):
        super().__init__(parent)
        self._label = label
        self._conn_type = conn_type
        self._idx = idx
        self._selected = False
        self._hovered = False
        self._connected = True
        self._close_hover = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(30)
        self.setStyleSheet("background: transparent; border: none;")
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(lambda pos: self.context_menu.emit(self._idx, pos))
        f = QFont("Segoe UI", 10)
        self.setFont(f)

    def set_selected(self, s):
        self._selected = s
        self.update()

    def set_connected(self, connected):
        self._connected = connected
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            tw = self.width()
            close_x = tw - 22
            if event.pos().x() >= close_x and self._hovered:
                self.close_clicked.emit(self._idx)
                return
        super().mousePressEvent(event)

    def enterEvent(self, e):
        self._hovered = True
        self.update()

    def leaveEvent(self, e):
        self._hovered = False
        self._close_hover = False
        self.update()

    def mouseMoveEvent(self, event):
        tw = self.width()
        self._close_hover = event.pos().x() >= tw - 22
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        color_hex = TAB_COLORS.get(self._conn_type, TAB_COLORS["default"])
        c = QColor(color_hex)

        if not self._connected:
            c = QColor("#f38ba8")

        if self._selected:
            painter.fillRect(r, QColor("#252639"))
            painter.setPen(QPen(c, 2))
            painter.drawLine(0, r.height() - 2, r.width(), r.height() - 2)
        elif self._hovered:
            painter.fillRect(r, QColor("#1e1e2e"))

        painter.setPen(QPen(c, 1.5))
        painter.setBrush(QBrush(c))
        painter.drawEllipse(8, r.height() // 2 - 3, 6, 6)

        painter.setPen(QColor("#cdd6f4") if self._selected else QColor("#6c7086"))
        painter.drawText(20, 0, r.width() - 44, r.height(),
                         Qt.AlignLeft | Qt.AlignVCenter, self._label)

        if self._hovered:
            cx, cy = r.width() - 16, r.height() // 2
            if self._close_hover:
                # Red background circle for close button hover
                painter.setBrush(QBrush(QColor("#f38ba8")))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(cx - 5, cy - 5, 10, 10)
                painter.setPen(QPen(QColor("#1e1e2e"), 1.5))
            else:
                painter.setPen(QPen(QColor("#6c7086"), 1.5))
            painter.drawLine(cx - 4, cy - 4, cx + 4, cy + 4)
            painter.drawLine(cx + 4, cy - 4, cx - 4, cy + 4)

        tw = painter.fontMetrics().horizontalAdvance(self._label) + 52
        self.setFixedWidth(tw)


class TabBarWidget(QFrame):
    tab_selected = Signal(int)
    tab_closed = Signal(int)
    new_tab = Signal()
    tab_context_menu = Signal(int, QPoint)
    tab_close_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setStyleSheet("background-color: #181825; border-bottom: 1px solid #313244;")
        self._tabs = []
        self._selected = -1

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(2)

        self._tab_container = QWidget()
        self._tab_container.setStyleSheet("background: transparent;")
        self._tab_layout = QHBoxLayout(self._tab_container)
        self._tab_layout.setContentsMargins(0, 0, 0, 0)
        self._tab_layout.setSpacing(2)
        self._tab_layout.addStretch()

        layout.addWidget(self._tab_container, 1)

        self._new_btn = QPushButton("+")
        self._new_btn.setFixedSize(24, 24)
        self._new_btn.setToolTip(tr("tab.new_connection_tooltip"))
        self._new_btn.setCursor(Qt.PointingHandCursor)
        self._new_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #6c7086;
                border: 1px solid #45475a; border-radius: 12px;
                font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #313244; color: #89b4fa; border-color: #89b4fa; }
        """)
        self._new_btn.clicked.connect(self.new_tab.emit)
        layout.addWidget(self._new_btn)

    def add_tab(self, label, conn_type="ssh"):
        idx = len(self._tabs)
        btn = ColorTabButton(label, conn_type, idx)
        btn.clicked.connect(lambda: self._select(idx))
        btn.context_menu.connect(lambda i, pos: self.tab_context_menu.emit(i, pos))
        btn.close_clicked.connect(lambda i: self.tab_close_clicked.emit(i))
        self._tab_layout.insertWidget(idx, btn)
        self._tabs.append(btn)
        self._select(idx)

    def set_tab_connected(self, idx, connected):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].set_connected(connected)

    def remove_tab(self, idx):
        if 0 <= idx < len(self._tabs):
            btn = self._tabs.pop(idx)
            self._tab_layout.removeWidget(btn)
            btn.deleteLater()
            # Re-index remaining buttons and reconnect signals
            for i, b in enumerate(self._tabs):
                b._idx = i
                # Disconnect old signals and reconnect with corrected index
                try:
                    b.clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                b.clicked.connect(lambda checked, ix=i: self._select(ix))
                try:
                    b.close_clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                b.close_clicked.connect(lambda ix=i: self.tab_close_clicked.emit(ix))
                try:
                    b.context_menu.disconnect()
                except (TypeError, RuntimeError):
                    pass
                b.context_menu.connect(lambda ix, pos: self.tab_context_menu.emit(ix, pos))
            if self._selected >= len(self._tabs):
                self._select(len(self._tabs) - 1)
            elif self._selected == idx:
                self._select(min(idx, len(self._tabs) - 1))

    def set_tab_label(self, idx, label):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]._label = label
            self._tabs[idx].update()

    def set_tab_type(self, idx, conn_type):
        if 0 <= idx < len(self._tabs):
            self._tabs[idx]._conn_type = conn_type
            self._tabs[idx].update()

    def select(self, idx):
        self._select(idx)

    def _select(self, idx):
        if self._selected >= 0 and self._selected < len(self._tabs):
            self._tabs[self._selected].set_selected(False)
        self._selected = idx
        if 0 <= idx < len(self._tabs):
            self._tabs[idx].set_selected(True)
            self.tab_selected.emit(idx)

    def count(self):
        return len(self._tabs)

    def clear(self):
        while self._tabs:
            btn = self._tabs.pop(0)
            self._tab_layout.removeWidget(btn)
            btn.deleteLater()
        self._selected = -1


class StatusBarWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        self.setStyleSheet("background-color: #11111b; border-top: 1px solid #313244;")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        sections = [
            ("status", tr("status.ready"), 120),
            ("mode", tr("status.remote"), 100),
            ("window", tr("status.window"), 100),
            ("cursor", tr("status.cursor"), 100),
            ("encoding", tr("status.encoding"), 100),
            ("time", "", 140),
        ]
        self._labels = {}
        for i, (key, text, w) in enumerate(sections):
            if i > 0:
                sep = QLabel("|")
                sep.setStyleSheet("color: #313244; font-size: 10px; padding: 0 4px; background: transparent;")
                layout.addWidget(sep)
            lbl = QLabel(text)
            lbl.setFixedWidth(w)
            lbl.setStyleSheet("color: #6c7086; font-size: 10px; background: transparent;")
            layout.addWidget(lbl)
            self._labels[key] = lbl

        layout.addStretch()

    def set_status(self, text, color="#a6e3a1"):
        self._labels["status"].setText(f"\u25cf {text}")
        self._labels["status"].setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")

    def set_window_size(self, w, h):
        self._labels["window"].setText(tr("status.window").format(w, h))

    def set_cursor_pos(self, row, col):
        self._labels["cursor"].setText(tr("status.cursor").format(row, col))

    def set_time(self, text):
        self._labels["time"].setText(text)

    def update_strings(self):
        self._labels["mode"].setText(tr("status.remote"))
        self._labels["encoding"].setText(tr("status.encoding"))


class SessionTab(QWidget):
    def __init__(self, connection, parent=None):
        super().__init__(parent)
        self.connection = connection
        self.terminal = TerminalWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.terminal)
        self.terminal.set_connection(connection)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(960, 640)
        self.resize(1280, 820)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setStyleSheet("""
            QMainWindow { background-color: #1a1b2e; }
            QMainWindow::separator { width: 0px; height: 0px; }
        """)

        self._sessions = []
        self._conn_type_map = {}
        self._reconnecting = set()
        # uid is a never-reused unique tab ID; the core identifier for all session state
        self._next_uid = 0
        self._uid_info = {}  # uid -> {tab_idx, conn_type, label, conn, saved_name?}
        self._tab_idx_to_uid = {}  # tab_widget idx -> uid

        central = QWidget()
        central.setObjectName("centralWidget")
        central.setStyleSheet("""
            QWidget#centralWidget {
                background-color: #1a1b2e;
                border-left: 1px solid #313244;
                border-bottom: 1px solid #313244;
                border-top: none;
                border-right: none;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        self.setCentralWidget(central)

        self.root_layout = QVBoxLayout(central)
        root = self.root_layout
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.setMenuWidget(self.title_bar)

        self._build_dock()
        self._load_saved_sessions()

        self.menu_bar = self._create_menu_bar()
        root.addWidget(self.menu_bar)

        self.color_tab_bar = TabBarWidget()
        self.color_tab_bar.tab_selected.connect(self._on_color_tab_selected)
        self.color_tab_bar.new_tab.connect(self._on_new_connection)
        self.color_tab_bar.tab_context_menu.connect(self._on_tab_context_menu)
        self.color_tab_bar.tab_close_clicked.connect(self._on_tab_close_clicked)
        root.addWidget(self.color_tab_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.terminal_area = QWidget()
        self.terminal_area.setStyleSheet("background: transparent;")

        term_layout = QVBoxLayout(self.terminal_area)
        term_layout.setContentsMargins(0, 0, 0, 0)
        term_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabBar().hide()
        self.tab_widget.currentChanged.connect(self._on_terminal_changed)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { background-color: #1a1b2e; border: none; }
        """)
        term_layout.addWidget(self.tab_widget, 1)

        self.send_panel = SendPanel()
        self.send_panel.send_command.connect(self._on_send_command)
        term_layout.addWidget(self.send_panel)

        body.addWidget(self.terminal_area, 1)

        root.addLayout(body, 1)

        self.quick_tags = QuickTagsBar()
        self.quick_tags.command_clicked.connect(self._on_quick_command)
        root.addWidget(self.quick_tags)

        self.status_bar = StatusBarWidget()
        root.addWidget(self.status_bar)

        self._update_time()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)

        self._apply_terminal_theme()
        self._restore_last_session()

    def _create_menu_bar(self):
        bar = QMenuBar()
        bar.setFixedHeight(28)
        bar.setStyleSheet("""
            QMenuBar {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border-bottom: 1px solid #313244;
                padding: 0 4px;
                font-size: 12px;
            }
            QMenuBar::item {
                padding: 4px 10px;
                border-radius: 4px;
            }
            QMenuBar::item:selected { background-color: #313244; }
            QMenu {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 24px; border-radius: 4px; }
            QMenu::item:selected { background-color: #45475a; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 8px; }
        """)

        def act(text, shortcut=None, callback=None):
            a = QAction(text, self)
            if shortcut:
                a.setShortcut(shortcut)
            if callback:
                a.triggered.connect(callback)
            return a

        session_menu = bar.addMenu(tr("menu.session"))
        session_menu.addAction(act(tr("menu.session.new"), "Ctrl+N", self._on_new_connection))
        session_menu.addAction(act(tr("menu.session.close"), "Ctrl+W", self._close_current))
        session_menu.addSeparator()
        session_menu.addAction(act(tr("menu.session.save"), "Ctrl+S", self._save_current_session))
        session_menu.addAction(act(tr("menu.session.disconnect_all"), "Ctrl+Shift+D", self._disconnect_all))
        session_menu.addSeparator()
        session_menu.addAction(act(tr("menu.session.exit"), "Ctrl+Q", self.close))

        edit_menu = bar.addMenu(tr("menu.edit"))
        edit_menu.addAction(act(tr("menu.edit.copy"), "Ctrl+Shift+C", self._on_copy))
        edit_menu.addAction(act(tr("menu.edit.paste"), "Ctrl+Shift+V", self._on_paste))
        edit_menu.addAction(act(tr("menu.edit.select_all"), "Ctrl+A", self._on_select_all))

        view_menu = bar.addMenu(tr("menu.view"))
        self._dock_action = self._dock.toggleViewAction()
        self._dock_action.setText(tr("menu.view.session_panel"))
        self._dock_action.setShortcut("Ctrl+B")
        view_menu.addAction(self._dock_action)
        view_menu.addSeparator()
        self._line_action = act(tr("menu.view.show_line_number"), None, self._toggle_line_numbers)
        self._line_action.setCheckable(True)
        self._line_action.setChecked(True)
        view_menu.addAction(self._line_action)
        view_menu.addAction(act(tr("menu.view.fullscreen"), "F11", self._toggle_fullscreen))

        tool_menu = bar.addMenu(tr("menu.tools"))
        tool_menu.addAction(act(tr("menu.tools.options"), "Ctrl+T", self._on_options))

        help_menu = bar.addMenu(tr("menu.help"))
        help_menu.addAction(act(tr("menu.help.about"), None, self._on_about))

        return bar

    def _build_dock(self):
        self._dock = QDockWidget(tr("session_panel.title"), self)
        self._dock.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self._dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self._dock.setFixedWidth(240)
        self._dock.setTitleBarWidget(QWidget())
        self._dock.setStyleSheet("""
            QDockWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: none;
                border-left: 1px solid #313244;
            }
        """)

        dock_content = QWidget()
        dock_content.setStyleSheet("background-color: #1e1e2e;")
        dl = QVBoxLayout(dock_content)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(0)

        self.session_panel = SessionTreePanel()
        self.session_panel.saved_session_clicked.connect(self._on_saved_session_click)
        self.session_panel.edit_saved.connect(self._on_edit_saved)
        dl.addWidget(self.session_panel, 1)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #313244;")
        dl.addWidget(sep)

        self.history_panel = HistoryPanel()
        self.history_panel.command_selected.connect(self._on_history_command)
        dl.addWidget(self.history_panel, 1)

        self._dock.setWidget(dock_content)
        self.addDockWidget(Qt.RightDockWidgetArea, self._dock)

    def _last_session_path(self):
        return os.path.join(get_data_dir(), "last_session.json")

    def _save_last_session(self, config, saved_name=None):
        data = {"config": config}
        if saved_name:
            data["saved_name"] = saved_name
        try:
            with open(self._last_session_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_last_session(self):
        try:
            with open(self._last_session_path(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _restore_last_session(self):
        data = self._load_last_session()
        if not data:
            return
        config = data.get("config")
        if not config or config.get("type") not in ("ssh", "serial", "telnet"):
            return
        saved_name = data.get("saved_name")
        self._start_connection(config, from_saved=saved_name)

    def _on_new_connection(self):
        dlg = ConnectionDialog(self)
        dlg.connection_requested.connect(self._start_connection)
        dlg.exec()

    def _start_connection(self, config, from_saved=None):
        debug(f"_start_connection type={config.get('type')} host={config.get('host')} port={config.get('port')} from_saved={from_saved}")
        # Always create a new tab — even if a tab with the same name already
        # exists.  The caller is responsible for not duplicating the right-side
        # saved-session list entry.
        try:
            conn = create_connection(config)
        except Exception as e:
            self.status_bar.set_status(f"Error: {e}", "#f38ba8")
            return
        conn_type = config.get("type", "ssh")
        label = config.get("display_name") or conn.display_name
        uid = self._next_uid
        self._next_uid += 1
        if from_saved:
            self.session_panel.update_saved_status(from_saved, "connected")
        self._save_last_session(config, from_saved)
        self._create_tab(conn, uid, label, conn_type, saved_name=from_saved)
        return uid

    def _create_tab(self, conn, uid, label, conn_type=None, saved_name=None):
        tab = SessionTab(conn)
        tab.terminal.set_session_name(label)
        idx = self.tab_widget.addTab(tab, label)
        self.tab_widget.setCurrentIndex(idx)
        if conn_type is None:
            conn_type = conn.config.get("type", "ssh")
        self._conn_type_map[idx] = conn_type
        self.color_tab_bar.add_tab(label, conn_type)
        # Store all state keyed by uid — saved_name tracked so disconnect can return the item to saved state
        info = {"tab_idx": idx, "label": label, "conn": conn, "conn_type": conn_type}
        if saved_name:
            info["saved_name"] = saved_name
        self._uid_info[uid] = info
        self._tab_idx_to_uid[idx] = uid
        tab._uid = uid
        # Connect signals using uid (never recycled)
        conn.connected.connect(lambda u=uid: self._on_tab_connected(u))
        conn.disconnected.connect(lambda msg, u=uid: self._on_tab_disconnected(u, msg))
        conn.error_occurred.connect(lambda msg, u=uid: self._on_tab_error(u, msg))
        tab.terminal.command_sent.connect(self.history_panel.add_command)
        debug(f"  create_tab idx={idx} uid={uid} label={label}")
        conn.start()
        self._sessions.append(tab)

    def _on_tab_connected(self, uid):
        debug(f"_on_tab_connected uid={uid}")
        info = self._uid_info.get(uid)
        if info is None:
            debug(f"  stale connected signal for uid {uid}")
            return
        idx = info["tab_idx"]
        self._reconnecting.discard(idx)
        cfg = info["conn"].config
        name = cfg.get("display_name") or info["conn"].display_name
        self.tab_widget.setTabText(idx, name)
        self.color_tab_bar.set_tab_label(idx, name)
        self.color_tab_bar.set_tab_connected(idx, True)
        saved_name = info.get("saved_name")
        if saved_name:
            self.session_panel.update_saved_status(saved_name, "connected")
        self.status_bar.set_status(name, "#a6e3a1")

    def _on_tab_disconnected(self, uid, msg):
        debug(f"_on_tab_disconnected uid={uid} msg={msg}")
        info = self._uid_info.get(uid)
        if info is None:
            debug(f"  stale disconnected signal for uid {uid}")
            return
        idx = info["tab_idx"]
        if idx in self._reconnecting:
            return
        if 0 <= idx < self.tab_widget.count():
            self.color_tab_bar.set_tab_connected(idx, False)
        saved_name = info.get("saved_name")
        if saved_name:
            self.session_panel.update_saved_status(saved_name, "disconnected")
        if idx == self.tab_widget.currentIndex():
            self.status_bar.set_status("Disconnected", "#f38ba8")

    def _on_tab_error(self, uid, msg):
        debug(f"_on_tab_error uid={uid} msg={msg}")
        info = self._uid_info.get(uid)
        if info is None:
            debug(f"  stale error signal for uid {uid}")
            return
        idx = info["tab_idx"]
        self._reconnecting.discard(idx)
        if 0 <= idx < self.tab_widget.count():
            self.color_tab_bar.set_tab_connected(idx, False)
        saved_name = info.get("saved_name")
        if saved_name:
            self.session_panel.update_saved_status(saved_name, "disconnected")
        if idx == self.tab_widget.currentIndex():
            self.status_bar.set_status(f"Error: {msg}", "#f38ba8")

    def _on_color_tab_selected(self, idx):
        if 0 <= idx < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(idx)

    def _on_tab_close_clicked(self, idx):
        """Bridge from TabBarWidget's idx-based close signal to uid-based _close_tab."""
        uid = self._tab_idx_to_uid.get(idx, -1)
        if uid >= 0:
            self._close_tab(uid)

    def _on_quick_command(self, text):
        tab = self.tab_widget.currentWidget()
        if tab and hasattr(tab, 'terminal') and tab.terminal._running and tab.terminal._connection:
            tab.terminal._connection.send(text + "\n")
            self.history_panel.add_command(text)

    def _on_terminal_changed(self, idx):
        self.color_tab_bar.select(idx)
        self._update_status_for_tab(idx)

    def _update_status_for_tab(self, idx):
        if idx < 0 or idx >= self.tab_widget.count():
            self.status_bar.set_status(tr("status.ready"), "#6c7086")
            return
        tab = self.tab_widget.widget(idx)
        if not tab or not hasattr(tab, 'terminal'):
            return
        if tab.terminal._running:
            name = tab.connection.display_name if hasattr(tab, 'connection') else ""
            cfg_name = ""
            if hasattr(tab, 'connection') and hasattr(tab.connection, 'config'):
                cfg_name = tab.connection.config.get("display_name", "")
            self.status_bar.set_status(cfg_name or name or tr("status.remote"), "#a6e3a1")
        else:
            self.status_bar.set_status(tr("status.disconnected"), "#f38ba8")

    def _load_saved_sessions(self):
        from .session_manager import list_sessions
        for name, data in list_sessions():
            conn_type = data.get("type", "ssh")
            self.session_panel.add_saved_session(name, conn_type)

    def _on_saved_session_click(self, name):
        debug(f"_on_saved_session_click name={name}")
        # Always open a new tab, even if a tab for this saved session already exists.
        from .session_manager import load_session
        data = load_session(name)
        if not data:
            return
        self._start_connection(data, from_saved=name)

    def _on_edit_saved(self, name, pos):
        from .session_manager import load_session, save_session
        from .connection_dialog import ConnectionDialog
        data = load_session(name)
        if not data:
            return
        menu = QMenu(self)
        menu.setStyleSheet(self._menu_style())
        edit_a = menu.addAction(tr("session_panel.edit_session"))
        delete_a = menu.addAction(tr("session_panel.delete_session"))
        action = menu.exec_(pos)
        if action == edit_a:
            dlg = ConnectionDialog(self, edit_data=data)
            if dlg.exec() == QDialog.Accepted and dlg._result:
                save_session(name, dlg._result)
        elif action == delete_a:
            from .session_manager import delete_session
            from PySide2.QtWidgets import QMessageBox
            r = QMessageBox.question(self, tr("session_panel.delete_session"),
                tr("session_panel.delete_confirm").format(name),
                QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes:
                delete_session(name)
                self.session_panel.remove_saved(name)

    def _edit_active_session(self, idx):
        if 0 <= idx < self.tab_widget.count():
            tab = self.tab_widget.widget(idx)
            if not tab or not hasattr(tab, 'connection'):
                return
            cfg = tab.connection.config
            from .connection_dialog import ConnectionDialog
            from .session_manager import save_session
            dlg = ConnectionDialog(self, edit_data=cfg)
            if dlg.exec() == QDialog.Accepted and dlg._result:
                new_cfg = dlg._result
                tab.connection.config = new_cfg
                name = new_cfg.get("display_name") or tab.connection.display_name
                self.tab_widget.setTabText(idx, name)
                self.color_tab_bar.set_tab_label(idx, name)
                if new_cfg.get("display_name"):
                    save_session(new_cfg["display_name"], new_cfg)

    def _exec_menu_clamped(self, menu, pos):
        w = self.window() if self.window() != self else self
        px = max(w.x(), min(pos.x(), w.x() + w.width() - menu.sizeHint().width()))
        py = max(w.y(), min(pos.y(), w.y() + w.height() - menu.sizeHint().height()))
        menu.exec_(QPoint(px, py))

    def _on_tab_context_menu(self, idx, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px; padding: 4px; font-size: 12px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #45475a; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 8px; }
        """)
        uid = self._tab_idx_to_uid.get(idx, -1)
        a_disconnect = menu.addAction(tr("context.disconnect"))
        a_disconnect.triggered.connect(lambda: self._disconnect_tab(uid))
        a_reconnect = menu.addAction(tr("context.reconnect"))
        a_reconnect.triggered.connect(lambda: self._reconnect_tab(uid))
        menu.addSeparator()
        a_close = menu.addAction(tr("context.close"))
        a_close.triggered.connect(lambda: self._close_tab(uid))
        self._exec_menu_clamped(menu, pos)

    def _disconnect_tab(self, uid):
        info = self._uid_info.get(uid)
        if info is None:
            return
        idx = info["tab_idx"]
        if 0 <= idx < self.tab_widget.count():
            tab = self.tab_widget.widget(idx)
            if tab:
                tab.terminal.disconnect()
                tab.connection.disconnect()
            saved_name = info.get("saved_name")
            if saved_name:
                self.session_panel.update_saved_status(saved_name, "disconnected")
            name = info["label"]
            self.color_tab_bar.set_tab_label(idx, name + " (off)")
            self.status_bar.set_status(tr("status.disconnected"), "#f38ba8")

    def _reconnect_tab(self, uid):
        debug(f"_reconnect_tab uid={uid}")
        info = self._uid_info.get(uid)
        if info is None:
            return
        idx = info["tab_idx"]
        if 0 <= idx < self.tab_widget.count():
            tab = self.tab_widget.widget(idx)
            if tab:
                self._reconnecting.add(idx)
                cfg = info["conn"].config
                tab.terminal.disconnect()
                info["conn"].disconnect()
                tab.terminal._closed = False
                tab.terminal.clear()
                tab.terminal._welcome()
                reconnect_label = cfg.get("display_name") or info["conn"].display_name
                tab.terminal._process_output(f"\x1b[32m\u2192 Reconnecting to {reconnect_label}...\x1b[0m\n")
                from .connections import create_connection
                new_conn = create_connection(cfg)
                new_conn.connected.connect(lambda u=uid: self._on_tab_connected(u))
                new_conn.disconnected.connect(lambda msg, u=uid: self._on_tab_disconnected(u, msg))
                new_conn.error_occurred.connect(lambda msg, u=uid: self._on_tab_error(u, msg))
                info["conn"] = new_conn
                tab.connection = new_conn
                tab.terminal.set_connection(new_conn)
                new_conn.start()
                self.tab_widget.setTabText(idx, reconnect_label)
                self.color_tab_bar.set_tab_label(idx, reconnect_label)
                self.status_bar.set_status(tr("status.reconnecting"), "#f9e2af")

    def _close_current(self):
        idx = self.tab_widget.currentIndex()
        uid = self._tab_idx_to_uid.get(idx, -1)
        if uid >= 0:
            self._close_tab(uid)

    def _on_send_command(self, text):
        tab = self.tab_widget.currentWidget()
        if tab and hasattr(tab, 'terminal') and hasattr(tab.terminal, '_running') and tab.terminal._running:
            lines = text.splitlines()
            for line in lines:
                if line.strip():
                    tab.terminal._connection.send(line + "\n")
                    self.history_panel.add_command(line.strip())

    def _on_history_command(self, cmd):
        self.send_panel.cmd_input.setPlainText(cmd)
        tab = self.tab_widget.currentWidget()
        if tab and hasattr(tab, 'terminal') and tab.terminal._running and tab.terminal._connection:
            tab.terminal._connection.send(cmd + "\n")
            self.history_panel.record_command(cmd)

    def _close_tab(self, uid):
        debug(f"_close_tab uid={uid}")
        info = self._uid_info.get(uid)
        if info is None:
            return
        idx = info["tab_idx"]
        tab = self.tab_widget.widget(idx) if 0 <= idx < self.tab_widget.count() else None
        if tab:
            tab.terminal.disconnect()
            info["conn"].disconnect()
        saved_name = info.get("saved_name")
        if saved_name:
            self.session_panel.update_saved_status(saved_name, "disconnected")
        self.color_tab_bar.remove_tab(idx)
        self.tab_widget.removeTab(idx)
        # Re-index _tab_idx_to_uid: shift entries after removed idx down
        del self._tab_idx_to_uid[idx]
        for i in range(idx + 1, self.tab_widget.count() + 1):
            if i in self._tab_idx_to_uid:
                self._tab_idx_to_uid[i - 1] = self._tab_idx_to_uid.pop(i)
        # If the uid had a _conn_type_map entry, clean it
        if idx in self._conn_type_map:
            del self._conn_type_map[idx]
        for i in range(idx + 1, self.tab_widget.count() + 1):
            if i in self._conn_type_map:
                self._conn_type_map[i - 1] = self._conn_type_map.pop(i)
        self._conn_type_map.pop(self.tab_widget.count(), None)
        # Update _uid_info for shifted tabs
        del self._uid_info[uid]
        for u, v in list(self._uid_info.items()):
            if v["tab_idx"] > idx:
                v["tab_idx"] -= 1
                self._tab_idx_to_uid[v["tab_idx"]] = u
        if tab in self._sessions:
            self._sessions.remove(tab)
            if self.tab_widget.count() == 0:
                self.status_bar.set_status("Ready", "#6c7086")
            else:
                self._update_status_for_tab(self.tab_widget.currentIndex())

    def _menu_style(self):
        return """
            QMenu { background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px; padding: 4px; font-size: 12px; }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background: #45475a; }
            QMenu::separator { height: 1px; background: #45475a; margin: 4px 8px; }
        """

    def _disconnect_all(self):
        # Close from the last tab backward – collect uids first since _close_tab mutates _uid_info
        uids = list(self._uid_info.keys())
        for uid in reversed(uids):
            self._close_tab(uid)

    def _save_current_session(self):
        tab = self.tab_widget.currentWidget()
        if not tab or not hasattr(tab, 'connection'):
            return
        from .session_manager import save_session
        cfg = tab.connection.config
        name = cfg.get("host", tab.connection.display_name)
        save_session(name, cfg)
        # Don't duplicate in the saved list
        for sname, _, _ in self.session_panel._saved_items:
            if sname == name:
                self.status_bar.set_status(f"Session saved: {name}", "#a6e3a1")
                return
        self.session_panel.add_saved_session(name, cfg.get("type", "ssh"))
        self.status_bar.set_status(f"Session saved: {name}", "#a6e3a1")

    def _current_terminal(self):
        tab = self.tab_widget.currentWidget()
        if tab and hasattr(tab, 'terminal'):
            return tab.terminal
        return None

    def _on_copy(self):
        term = self._current_terminal()
        if term:
            term.copy()

    def _on_paste(self):
        term = self._current_terminal()
        if term and term._running and term._connection:
            from PySide2.QtWidgets import QApplication
            text = QApplication.clipboard().text()
            if text:
                term._connection.send(text)

    def _on_select_all(self):
        term = self._current_terminal()
        if term:
            term.selectAll()

    def _toggle_line_numbers(self):
        term = self._current_terminal()
        if term:
            term._line_numbers = not term._line_numbers
            term._update_line_number_width()

    def _apply_terminal_theme(self):
        bg, fg, sel_bg, sel_fg = "#1a1b2e", "#cdd6f4", "#89b4fa", "#1e1e2e"
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab and hasattr(tab, 'terminal'):
                tab.terminal.apply_theme_colors(bg, fg, sel_bg, sel_fg)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_options(self):
        from .options_dialog import OptionsDialog
        dlg = OptionsDialog(self)
        dlg.exec()

    def _on_about(self):
        import datetime
        from PySide2.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
        from PySide2.QtGui import QPixmap, QFont
        from PySide2.QtCore import Qt
        dlg = QDialog(self)
        dlg.setWindowTitle(tr("menu.help.about"))
        dlg.setFixedSize(360, 380)
        dlg.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4;")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(8)
        pix = QPixmap(os.path.join(get_app_dir(), "Rat.png"))
        if not pix.isNull():
            icon_label = QLabel()
            icon_label.setPixmap(pix.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
        title_label = QLabel(f"<b style='font-size:18px'>{APP_NAME}</b>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        year = datetime.datetime.now().year
        info = QLabel(
            f"<div style='text-align:center; line-height:1.8; font-size:13px;'>"
            f"<b>Author:</b> Rat<br>"
            f"<b>Version:</b> {APP_VERSION}<br>"
            f"<b>Date:</b> {year}<br>"
            f"<b>License:</b> LGPL<br><br>"
            f"SSH / Serial / Telnet terminal<br>"
            f"Built with PySide2</div>"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)
        layout.addStretch()
        btn = QPushButton(tr("dialog.ok"))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 8px 32px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """)
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn, 0, Qt.AlignCenter)
        dlg.exec()

    def _toggle_language(self):
        from .i18n import set_language, current_language, tr as _
        new_lang = "en" if current_language() == "zh" else "zh"
        set_language(new_lang)
        self._rebuild_ui_strings()

    def _rebuild_ui_strings(self):
        self.title_bar.set_title(tr("title_bar.title"))
        for i in range(self.root_layout.count()):
            w = self.root_layout.itemAt(i).widget()
            if w is self.menu_bar:
                new_bar = self._create_menu_bar()
                self.root_layout.insertWidget(i, new_bar)
                self.root_layout.removeWidget(self.menu_bar)
                self.menu_bar.deleteLater()
                self.menu_bar = new_bar
                break
        self._dock.setWindowTitle(tr("session_panel.title"))
        self.status_bar.update_strings()
        self.send_panel.update_strings()
        self.session_panel.update_strings()
        self.history_panel.update_strings()

    def closeEvent(self, event):
        self._disconnect_all()
        import time
        time.sleep(0.2)
        event.accept()

    def _update_time(self):
        from datetime import datetime
        self.status_bar.set_time(datetime.now().strftime("%Y/%m/%d  %H:%M:%S"))
