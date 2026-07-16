import os
import re
import datetime
import pyte
import wcwidth
from PySide2.QtWidgets import (
    QWidget, QApplication, QMenu, QScrollBar, QFileDialog,
    QHBoxLayout, QLineEdit, QPushButton, QLabel, QAction
)
from PySide2.QtCore import Qt, Signal, QRect, QTimer, QPoint, QUrl
from PySide2.QtGui import QColor, QFont, QFontMetrics, QFontDatabase, QPainter, QClipboard, QDesktopServices, QPixmap, QIcon
from .i18n import tr
from .resources import APP_NAME, APP_VERSION, get_data_dir
from .log_manager import LogManager
from .logger import debug

_STYLE = """
    QMenu { background: #313244; color: #cdd6f4;
        border: 1px solid #45475a; border-radius: 6px; padding: 4px; font-size: 12px; }
    QMenu::item { padding: 6px 24px; border-radius: 4px; }
    QMenu::item:selected { background: #45475a; }
    QMenu::item:disabled { color: #585b70; }
    QMenu::separator { height: 1px; background: #45475a; margin: 4px 8px; }
"""


class SearchBar(QWidget):
    def __init__(self, terminal):
        super().__init__(terminal)
        self._terminal = terminal
        self.setFixedHeight(36)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #1e1e2e;")
        hl = QHBoxLayout(self)
        hl.setContentsMargins(8, 2, 8, 2)
        hl.setSpacing(6)

        self._input = QLineEdit()
        self._input.setPlaceholderText(tr("search.placeholder"))
        self._input.setStyleSheet("""
            QLineEdit {
                background: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a;
                border-radius: 4px; padding: 4px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        self._input.setFixedWidth(200)

        # Aa toggle inside the search input
        self._case_act = QAction(self)
        self._case_act.setToolTip("Aa")
        self._case_act.setData(False)
        self._update_case_icon()
        self._input.addAction(self._case_act, QLineEdit.TrailingPosition)

        hl.addWidget(self._input)

        self._prev = QPushButton(tr("search.prev"))
        self._prev.setStyleSheet("""
            QPushButton { background: transparent; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: #313244; color: #89b4fa; border-color: #89b4fa; }
        """)
        hl.addWidget(self._prev)

        self._next = QPushButton(tr("search.next"))
        self._next.setStyleSheet("""
            QPushButton { background: transparent; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: #313244; color: #89b4fa; border-color: #89b4fa; }
        """)
        hl.addWidget(self._next)

        self._label = QLabel("0/0")
        self._label.setStyleSheet("color: #6c7086; font-size: 11px; background: transparent;")
        hl.addWidget(self._label)

        self._close = QPushButton(tr("search.close"))
        self._close.setStyleSheet("""
            QPushButton { background: transparent; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 2px 8px; font-size: 11px; }
            QPushButton:hover { background: #f38ba8; color: #1e1e2e; border-color: #f38ba8; }
        """)
        hl.addWidget(self._close)

    def _update_case_icon(self):
        active = self._case_act.data()
        px = QPixmap(20, 20)
        px.fill(Qt.transparent)
        p = QPainter(px)
        if active:
            p.fillRect(px.rect(), QColor("#89b4fa"))
            p.setPen(QColor("#1e1e2e"))
        else:
            p.setPen(QColor("#6c7086"))
        f = QFont("Segoe UI", 9, QFont.Bold)
        p.setFont(f)
        p.drawText(px.rect(), Qt.AlignCenter, "Aa")
        p.end()
        self._case_act.setIcon(QIcon(px))


def _brighten(c, amount=0.35):
    r = min(255, int(c.red() + (255 - c.red()) * amount))
    g = min(255, int(c.green() + (255 - c.green()) * amount))
    b = min(255, int(c.blue() + (255 - c.blue()) * amount))
    return QColor(r, g, b)

_ANSI_COLORS = {
    0:  QColor("#1e1e2e"),
    1:  QColor("#f38ba8"),
    2:  QColor("#a6e3a1"),
    3:  QColor("#f9e2af"),
    4:  QColor("#89b4fa"),
    5:  QColor("#f5c2e7"),
    6:  QColor("#94e2d5"),
    7:  QColor("#bac2de"),
    8:  _brighten(QColor("#585b70"), 0.5),
    9:  _brighten(QColor("#f38ba8"), 0.35),
    10: _brighten(QColor("#a6e3a1"), 0.35),
    11: _brighten(QColor("#f9e2af"), 0.35),
    12: _brighten(QColor("#89b4fa"), 0.35),
    13: _brighten(QColor("#f5c2e7"), 0.35),
    14: _brighten(QColor("#94e2d5"), 0.35),
    15: QColor("#cdd6f4"),
}

_NAMED_COLORS = {
    "black": QColor("#1e1e2e"),
    "red": QColor("#f38ba8"),
    "green": QColor("#a6e3a1"),
    "brown": QColor("#f9e2af"),
    "blue": QColor("#89b4fa"),
    "magenta": QColor("#f5c2e7"),
    "cyan": QColor("#94e2d5"),
    "lightgray": QColor("#bac2de"),
    "darkgray": QColor("#585b70"),
    "lightred": QColor("#f38ba8"),
    "lightgreen": QColor("#a6e3a1"),
    "yellow": QColor("#f9e2af"),
    "lightblue": QColor("#89b4fa"),
    "lightmagenta": QColor("#f5c2e7"),
    "lightcyan": QColor("#94e2d5"),
    "white": QColor("#cdd6f4"),
}

for _name, _color in list(_NAMED_COLORS.items()):
    _NAMED_COLORS["bright" + _name] = _brighten(_color)


def _xterm256_to_qcolor(code):
    if code < 16:
        return _ANSI_COLORS[code]
    if code < 232:
        code -= 16
        r = (code // 36) * 40 + 55 if code // 36 else 0
        g = ((code % 36) // 6) * 40 + 55 if ((code % 36) // 6) else 0
        b = (code % 6) * 40 + 55 if code % 6 else 0
        return QColor(r, g, b)
    gray = (code - 232) * 10 + 8
    return QColor(gray, gray, gray)


def _in_selection(start, end, row, col):
    if start is None or end is None:
        return False
    r1, c1 = start
    r2, c2 = end
    if r1 > r2 or (r1 == r2 and c1 > c2):
        r1, c1, r2, c2 = r2, c2, r1, c1
    if row < r1 or row > r2:
        return False
    if row == r1 and row == r2:
        return c1 <= col <= c2
    if row == r1:
        return col >= c1
    if row == r2:
        return col <= c2
    return True


def _pyte_color_to_qcolor(color_spec, default):
    if color_spec == "default":
        return default
    if isinstance(color_spec, int):
        return _xterm256_to_qcolor(color_spec)
    if isinstance(color_spec, tuple) and len(color_spec) == 3:
        return QColor(*color_spec)
    if isinstance(color_spec, str):
        return _NAMED_COLORS.get(color_spec.lower(), default)
    return default


class LineNumberArea(QWidget):
    def __init__(self, terminal):
        super().__init__(terminal)
        self._terminal = terminal

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#181825"))
        t = self._terminal
        if not t._screen:
            return
        screen = t._screen
        ch = t._char_height
        start = t._get_view_start()
        for i in range(screen.lines):
            y = i * ch
            if y + ch < event.rect().top() or y > event.rect().bottom():
                continue
            painter.setPen(QColor("#585b70"))
            painter.setFont(t._font)
            painter.drawText(QRect(0, y, self.width() - 4, ch),
                             Qt.AlignRight | Qt.AlignVCenter, str(start + i + 1))

    def sizeHint(self):
        return self._terminal._line_number_width()


class TerminalWidget(QWidget):
    output_received = Signal(str)
    connected = Signal()
    disconnected = Signal(str)
    connection_error = Signal(str)
    command_sent = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._connection = None
        self._running = False
        self._closed = False

        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        font.setPointSize(11)
        font.setFamilies(["Cascadia Code", "JetBrains Mono", "Consolas", "Courier New"])
        self._font = font
        fm = QFontMetrics(font)
        self._char_width = fm.horizontalAdvance("W")
        self._char_height = fm.height()

        self._screen = pyte.HistoryScreen(200, 24, history=10000)
        self._stream = pyte.Stream(self._screen)

        self._cursor_visible = True
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._toggle_cursor)
        self._cursor_timer.start(500)

        self._line_numbers = True
        self._line_number_area = LineNumberArea(self)

        self._bg_color = QColor("#1a1b2e")
        self._fg_color = QColor("#cdd6f4")
        self._sel_bg = QColor("#89b4fa")
        self._sel_fg = QColor("#1e1e2e")

        self._cmd_buffer = ""

        self._sel_start = None
        self._sel_end = None
        self._selecting = False

        self._scroll_offset = 0
        self._scrollbar = QScrollBar(Qt.Vertical, self)
        self._scrollbar.valueChanged.connect(self._on_scroll)

        self._search_bar = None
        self._search_keyword = ""
        self._search_case = False
        self._search_matches = []
        self._search_idx = -1

        self._log_manager = LogManager()
        self._session_name = tr("app.name")

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #1a1b2e;")

        self._welcome()

    def focusNextPrevChild(self, next_child):
        """Prevent Tab/Shift+Tab from moving focus away from the terminal.
        The Tab key must be sent to the remote connection, not used for Qt
        widget navigation."""
        return False

    def _line_number_width(self):
        if not self._line_numbers or not self._screen:
            return 0
        digits = len(str(max(1, self._screen.lines)))
        return 8 + 12 * digits

    def _update_line_number_width(self):
        self._line_number_area.setVisible(self._line_numbers)
        cr = self.contentsRect()
        lnw = self._line_number_width()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), lnw, cr.height()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_buffer()
        cr = self.contentsRect()
        lnw = self._line_number_width()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), lnw, cr.height()))
        sbw = self._scrollbar.sizeHint().width()
        self._scrollbar.setGeometry(QRect(cr.right() - sbw, cr.top(), sbw, cr.height()))
        self._update_scrollbar()

    def _resize_buffer(self):
        if not self._screen or self._char_height <= 0:
            return
        w = self.width()
        h = self.height()
        if w < 1 or h < 1:
            return
        cols = max(20, (w - self._line_number_width()) // self._char_width)
        rows = max(5, h // self._char_height)
        if cols == self._screen.columns and rows == self._screen.lines:
            return

        old_rows = self._screen.lines
        saved = {}
        if rows < old_rows:
            # Save buffer content before shrink: pyte.resize discards real
            # content at the top and keeps empty lines from prior expansion.
            for y in range(old_rows):
                if y in self._screen.buffer:
                    saved[y] = dict(self._screen.buffer[y].items())

        self._screen.resize(rows, cols)

        if saved:
            # Restore real content column by column (line objects are
            # StaticDefaultDict, not plain lists, so we mustn't replace them).
            count = min(rows, len(saved))
            for y in range(count):
                if y in saved:
                    for col, char in saved[y].items():
                        self._screen.buffer[y][col] = char

        self._scroll_to_bottom()

    def paintEvent(self, event):
        if not self._screen:
            return
        painter = QPainter(self)
        painter.setFont(self._font)
        painter.fillRect(self.rect(), self._bg_color)

        if not self._screen:
            return

        screen = self._screen
        ch = self._char_height
        cw = self._char_width
        lnw = self._line_number_width()
        sbw = self._scrollbar.sizeHint().width()
        vis_cols = max(20, (self.width() - lnw) // cw) if cw else screen.columns

        all_lines = []
        if screen.history.top is not None:
            for row in screen.history.top:
                all_lines.append(row)
        for y in range(screen.lines):
            all_lines.append(screen.buffer[y])

        vis = screen.lines
        total = len(all_lines)
        start = self._get_view_start()

        sel_start = self._sel_start
        sel_end = self._sel_end
        has_sel = sel_start is not None and sel_end is not None

        for y in range(vis):
            src_idx = start + y
            if src_idx >= total:
                break
            row = all_lines[src_idx]
            py = y * ch
            x = 0
            while x < vis_cols:
                char = row[x]
                w = max(1, wcwidth.wcwidth(char.data))
                cw_char = cw * w
                px = lnw + x * cw
                bg = _pyte_color_to_qcolor(char.bg, self._bg_color)
                fg = _pyte_color_to_qcolor(char.fg, self._fg_color)
                if char.reverse:
                    painter.fillRect(px, py, int(cw_char), ch, fg)
                elif bg != self._bg_color:
                    painter.fillRect(px, py, int(cw_char), ch, bg)

                if self._search_matches and self._is_in_match(src_idx, x):
                    if self._is_current_match(src_idx, x):
                        painter.fillRect(px, py, int(cw_char), ch, QColor("#f9a825"))
                    else:
                        painter.fillRect(px, py, int(cw_char), ch, QColor("#f9e2af"))

                if char.data not in (" ", "", None):
                    fg_color = _pyte_color_to_qcolor(char.fg, self._fg_color)
                    if char.reverse:
                        fg_color = self._bg_color
                    if self._search_matches and self._is_in_match(src_idx, x):
                        if self._is_current_match(src_idx, x):
                            fg_color = QColor("#1e1e2e")
                        else:
                            fg_color = QColor("#1e1e2e")
                    elif has_sel and _in_selection(sel_start, sel_end, y, x):
                        painter.fillRect(px, py, int(cw_char), ch, self._sel_bg)
                        fg_color = self._sel_fg
                    if char.bold or char.italics or char.underscore:
                        f = QFont(self._font)
                        f.setBold(char.bold)
                        f.setItalic(char.italics)
                        f.setUnderline(char.underscore)
                        painter.setFont(f)
                    else:
                        painter.setFont(self._font)
                    painter.setPen(fg_color)
                    painter.drawText(px, py, int(cw_char), ch,
                                     Qt.AlignLeft | Qt.AlignVCenter, char.data)

                x += w

        if self._cursor_visible and self.hasFocus() and self._scroll_offset == 0:
            cx = screen.cursor.x
            cy = screen.cursor.y
            if 0 <= cy < screen.lines and 0 <= cx < screen.columns:
                char = screen.buffer[cy][cx]
                w = max(1, wcwidth.wcwidth(char.data))
                cw_char = cw * w
                px = lnw + cx * cw
                py = cy * ch
                painter.fillRect(px, py, int(cw_char), ch, self._sel_bg)
                if char.data not in (" ", "", None):
                    painter.setPen(self._bg_color)
                    painter.drawText(px, py, int(cw_char), ch,
                                     Qt.AlignLeft | Qt.AlignVCenter, char.data)

    def _toggle_cursor(self):
        self._cursor_visible = not self._cursor_visible
        self.update()

    def _total_visible_lines(self):
        if not self._screen:
            return 0
        h = self._screen.history
        hist_lines = len(h.top) if h.top is not None else 0
        return hist_lines + self._screen.lines

    def _get_view_start(self):
        if not self._screen:
            return 0
        total = self._total_visible_lines()
        if self._scroll_offset == 0:
            return max(0, total - self._screen.lines)
        start = max(0, total - self._screen.lines - self._scroll_offset)
        return max(0, min(start, total - self._screen.lines))

    def _update_scrollbar(self):
        total = self._total_visible_lines()
        vis = self._screen.lines if self._screen else 0
        max_scroll = max(0, total - vis)
        self._scrollbar.setRange(0, max_scroll)
        self._scrollbar.setValue(max_scroll - self._scroll_offset)
        self._scrollbar.setPageStep(vis)
        self._scrollbar.setSingleStep(1)

    def _on_scroll(self, value):
        total = self._total_visible_lines()
        vis = self._screen.lines if self._screen else 0
        max_scroll = max(0, total - vis)
        self._scroll_offset = max_scroll - value
        self.update()

    def _scroll_to_bottom(self):
        if self._scroll_offset != 0:
            self._scroll_offset = 0
            total = self._total_visible_lines()
            vis = self._screen.lines if self._screen else 0
            self._scrollbar.setValue(max(0, total - vis))
            self.update()

    def wheelEvent(self, event):
        if not self._screen:
            return
        total = self._total_visible_lines()
        vis = self._screen.lines
        max_scroll = max(0, total - vis)
        delta = event.angleDelta().y()
        steps = delta // 120
        self._scroll_offset = max(0, min(max_scroll, self._scroll_offset + steps))
        self._scrollbar.setValue(max_scroll - self._scroll_offset)
        self.update()

    def set_connection(self, conn):
        if self._connection:
            try:
                self._connection.output_received.disconnect(self._on_data)
                self._connection.connected.disconnect(self._on_connected)
                self._connection.disconnected.disconnect(self._on_disconnected)
                self._connection.error_occurred.disconnect(self._on_error)
            except (TypeError, RuntimeError):
                pass
        self._connection = conn
        conn.output_received.connect(self._on_data)
        conn.connected.connect(self._on_connected)
        conn.disconnected.connect(self._on_disconnected)
        conn.error_occurred.connect(self._on_error)

    def _on_connected(self):
        self._running = True
        self.connected.emit()

    def _on_disconnected(self, msg):
        self._running = False
        self._process_output(f"\x1b[33m\u26a0 Connection closed: {msg}\x1b[0m\r\n")
        self.disconnected.emit(msg)

    def _on_error(self, msg):
        self._running = False
        self._process_output(f"\x1b[31m\u2716 Error: {msg}\x1b[0m\r\n")
        self.connection_error.emit(msg)

    def _on_data(self, text):
        if not self._closed:
            self._log_manager.write(text)
            self._process_output(text)

    def _process_output(self, text):
        if not self._screen or not self._stream:
            return
        self._stream.feed(text)
        self._scroll_to_bottom()
        self._update_scrollbar()
        if self._search_bar and self._search_bar.isVisible() and self._search_keyword:
            self._do_search()
        self.update()

    def _welcome(self):
        subtitle = tr("terminal.welcome_subtitle")
        hint = tr("terminal.welcome_hint")
        title_line = f"{APP_NAME} v{APP_VERSION}"
        texts = [title_line, subtitle, hint]
        w = lambda s: sum(max(1, wcwidth.wcwidth(c)) for c in s)
        max_w = max(w(t) for t in texts)
        box_w = max(24, max_w + 8)

        cat = [
            "  .--,       .--,",
            " ( (  \\.---./  ) )",
            "  '.__/o   o\\__.'",
            "     {=  ^  =}",
            "      >  -  <",
        ]
        cat_w = max(len(l) for l in cat)
        box_w = max(box_w, cat_w + 4)
        indent = max(0, (box_w - cat_w) // 2)

        horiz = "\u2500" * (box_w - 4)
        lines = [""]
        for l in cat:
            lines.append("\x1b[96m" + " " * (indent + 2) + l + "\x1b[0m")
        lines.append(f"\x1b[94m  \u250c{horiz}\u2510")
        for t in texts:
            pad = box_w - 8 - w(t)
            inner = "\x1b[96m   " + t + " " * pad + " \x1b[94m"
            lines.append(f"\x1b[94m  \u2502{inner}\u2502\x1b[0m")
        lines.append(f"\x1b[94m  \u2514{horiz}\u2518\x1b[0m")
        welcome = "\r\n".join(lines) + "\r\n"
        self._process_output(welcome)

    def clear(self):
        self._screen = pyte.HistoryScreen(
            self._screen.columns, self._screen.lines, history=10000
        )
        self._stream = pyte.Stream(self._screen)
        self._scroll_offset = 0
        self._update_scrollbar()
        self.update()

    def connect_to(self, conn):
        self._closed = False
        self.clear()
        self._welcome()
        self._process_output(f"\x1b[32m\u2192 Connecting to {conn}...\x1b[0m\n")
        self.set_connection(conn)

    def disconnect(self):
        self._closed = True
        if self._connection:
            self._connection.disconnect()

    def close(self):
        self.disconnect()
        super().close()

    def apply_theme_colors(self, bg="#1a1b2e", fg="#cdd6f4", sel_bg="#89b4fa", sel_fg="#1e1e2e"):
        self._bg_color = QColor(bg)
        self._fg_color = QColor(fg)
        self._sel_bg = QColor(sel_bg)
        self._sel_fg = QColor(sel_fg)
        self.update()

    def set_session_name(self, name):
        self._session_name = name

    def copy(self):
        if not self._screen:
            return
        clipboard = QApplication.clipboard()
        clipboard.setText(self._get_selected_text())

    def selectAll(self):
        if not self._screen:
            return
        self._sel_start = (0, 0)
        self._sel_end = (self._screen.lines - 1, self._screen.columns - 1)
        self.update()

    def _get_view_start(self):
        if not self._screen:
            return 0
        total = self._total_visible_lines()
        vis = self._screen.lines
        if self._scroll_offset == 0:
            return max(0, total - vis)
        start = max(0, total - vis - self._scroll_offset)
        return max(0, min(start, total - vis))

    def _get_selected_text(self):
        if not self._screen or self._sel_start is None or self._sel_end is None:
            return ""
        all_lines = []
        if self._screen.history.top is not None:
            for row in self._screen.history.top:
                all_lines.append(row)
        for y in range(self._screen.lines):
            all_lines.append(self._screen.buffer[y])
        start = self._get_view_start()

        r1, c1 = self._sel_start
        r2, c2 = self._sel_end
        if r1 > r2 or (r1 == r2 and c1 > c2):
            r1, c1, r2, c2 = r2, c2, r1, c1
        lines = []
        for y in range(r1, r2 + 1):
            row = all_lines[start + y]
            a = c1 if y == r1 else 0
            b = c2 if y == r2 else self._screen.columns - 1
            text = "".join(row[x].data for x in range(a, b + 1)).rstrip()
            lines.append(text)
        return "\n".join(lines)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet(_STYLE)
        menu.addAction(tr("menu.edit.copy"), self.copy)
        menu.addAction(tr("menu.edit.paste"), self.paste)
        menu.addSeparator()
        menu.addAction(tr("menu.edit.find"), self._toggle_search)
        menu.addSeparator()
        menu.addAction(tr("menu.edit.select_all"), self.selectAll)
        menu.addSeparator()
        log_menu = menu.addMenu(tr("log.menu"))
        log_menu.setStyleSheet(_STYLE)
        log_start = log_menu.addAction(tr("log.start"))
        log_stop = log_menu.addAction(tr("log.stop"))
        log_start.setEnabled(not self._log_manager.is_active)
        log_stop.setEnabled(self._log_manager.is_active)
        log_menu.addSeparator()
        log_open = log_menu.addAction(tr("log.open_folder"))
        log_start.triggered.connect(self._log_start)
        log_stop.triggered.connect(self._log_stop)
        log_open.triggered.connect(self._log_open_folder)
        menu.exec_(QPoint(
            min(event.globalPos().x(), self.window().x() + self.window().width() - menu.sizeHint().width()),
            min(event.globalPos().y(), self.window().y() + self.window().height() - menu.sizeHint().height())
        ))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._screen:
            lnw = self._line_number_width()
            x = int((event.pos().x() - lnw) // self._char_width)
            y = int(event.pos().y() // self._char_height)
            x = max(0, min(x, self._screen.columns - 1))
            y = max(0, min(y, self._screen.lines - 1))
            self._sel_start = (y, x)
            self._sel_end = (y, x)
            self._selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self._selecting and self._screen:
            lnw = self._line_number_width()
            x = int((event.pos().x() - lnw) // self._char_width)
            y = int(event.pos().y() // self._char_height)
            x = max(0, min(x, self._screen.columns - 1))
            y = max(0, min(y, self._screen.lines - 1))
            self._sel_end = (y, x)
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._selecting = False

    def keyPressEvent(self, event):
        if not self._running or not self._connection:
            super().keyPressEvent(event)
            return

        self._scroll_to_bottom()
        key = event.key()
        mod = event.modifiers()
        text = event.text()

        if key == Qt.Key_C and mod == Qt.ControlModifier:
            self._connection.send("\x03")
            return

        if key == Qt.Key_V and mod == Qt.ControlModifier:
            self.paste()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            self._connection.send("\r")
            cmd = self._cmd_buffer.strip()
            if cmd:
                self.command_sent.emit(cmd)
            self._cmd_buffer = ""
            return

        if key == Qt.Key_Backspace:
            self._connection.send("\x7f")
            self._cmd_buffer = self._cmd_buffer[:-1]
            return

        if key == Qt.Key_Tab:
            self._connection.send("\t")
            return

        if key == Qt.Key_Up:
            self._connection.send("\x1b[A")
            self._cmd_buffer = ""
            return
        if key == Qt.Key_Down:
            self._connection.send("\x1b[B")
            self._cmd_buffer = ""
            return
        if key == Qt.Key_Left:
            self._connection.send("\x1b[D")
            return
        if key == Qt.Key_Right:
            self._connection.send("\x1b[C")
            return
        if key == Qt.Key_Delete:
            self._connection.send("\x1b[3~")
            return
        if key == Qt.Key_Home:
            self._connection.send("\x1b[H")
            return
        if key == Qt.Key_End:
            self._connection.send("\x1b[F")
            return
        if key in (Qt.Key_PageUp, Qt.Key_PageDown):
            return
        if key == Qt.Key_Escape:
            self._connection.send("\x1b")
            return
        if key == Qt.Key_Insert:
            return

        if mod == Qt.ControlModifier:
            if key == Qt.Key_Z:
                self._connection.send("\x1a")
            elif key == Qt.Key_D:
                self._connection.send("\x04")
            elif key == Qt.Key_A:
                self._connection.send("\x01")
            elif key == Qt.Key_E:
                self._connection.send("\x05")
            elif key == Qt.Key_W:
                self._connection.send("\x17")
            elif key == Qt.Key_U:
                self._connection.send("\x15")
            elif key == Qt.Key_K:
                self._connection.send("\x0b")
            elif key == Qt.Key_L:
                self._connection.send("\x0c")
            elif key == Qt.Key_R:
                self._connection.send("\x12")
            elif key == Qt.Key_Q:
                self._connection.send("\x11")
            elif key == Qt.Key_S:
                self._connection.send("\x13")
            return

        if Qt.Key_F1 <= key <= Qt.Key_F4:
            self._connection.send(f"\x1bO{chr(80 + key - Qt.Key_F1)}")
            return
        if key == Qt.Key_F5:
            self._connection.send("\x1b[15~")
            return
        if key == Qt.Key_F6:
            self._connection.send("\x1b[17~")
            return
        if key == Qt.Key_F7:
            self._connection.send("\x1b[18~")
            return
        if key == Qt.Key_F8:
            self._connection.send("\x1b[19~")
            return
        if key == Qt.Key_F9:
            self._connection.send("\x1b[20~")
            return
        if key == Qt.Key_F10:
            self._connection.send("\x1b[21~")
            return
        if key == Qt.Key_F11:
            self._connection.send("\x1b[23~")
            return
        if key == Qt.Key_F12:
            self._connection.send("\x1b[24~")
            return

        if text:
            self._connection.send(text)
            self._cmd_buffer += text

    def paste(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self._connection.send(text)

    def _toggle_search(self):
        if self._search_bar and self._search_bar.isVisible():
            self._search_close()
        else:
            self._show_search_bar()

    def _show_search_bar(self):
        if not self._search_bar:
            self._search_bar = SearchBar(self)
            self._search_bar._input.textChanged.connect(self._on_search_text)
            self._search_bar._prev.clicked.connect(self._search_prev)
            self._search_bar._next.clicked.connect(self._search_next)
            self._search_bar._case_act.triggered.connect(self._on_toggle_case)
            self._search_bar._close.clicked.connect(self._search_close)
        self._search_bar.show()
        self._search_bar.raise_()
        self._search_bar._input.setFocus()
        self._search_bar._input.selectAll()

    def _search_close(self):
        if self._search_bar:
            self._search_bar.hide()
        self._search_keyword = ""
        self._search_matches = []
        self._search_idx = -1
        self.setFocus()
        self.update()

    def _on_toggle_case(self):
        if self._search_bar:
            active = not self._search_bar._case_act.data()
            self._search_bar._case_act.setData(active)
            self._search_bar._update_case_icon()
        self._on_search_text()

    def _on_search_text(self, checked=None):
        keyword = self._search_bar._input.text() if self._search_bar else ""
        self._search_case = bool(self._search_bar._case_act.data()) if self._search_bar else False
        # Close on empty escape sequence - handled by Esc in SearchBar
        self._search_keyword = keyword
        self._do_search()
        self.update()

    def _do_search(self):
        self._search_matches = []
        self._search_idx = -1
        kw = self._search_keyword
        if not kw or not self._screen:
            self._update_search_label()
            return
        all_lines = []
        if self._screen.history.top is not None:
            for row in self._screen.history.top:
                all_lines.append(row)
        for y in range(self._screen.lines):
            all_lines.append(self._screen.buffer[y])
        flags = 0 if self._search_case else re.IGNORECASE
        for global_y, row in enumerate(all_lines):
            col_of_char = []
            keep = []
            for x in range(self._screen.columns):
                d = row[x].data
                if d == "":
                    continue
                col_of_char.append(x)
                keep.append(d)
            text = "".join(keep)
            pos = 0
            while True:
                m = re.search(re.escape(kw), text[pos:], flags)
                if not m:
                    break
                c1 = pos + m.start()
                c2 = pos + m.end()
                col_start = col_of_char[c1] if c1 < len(col_of_char) else c1
                col_end = col_of_char[c2 - 1] + 1 if c2 - 1 < len(col_of_char) else c2
                self._search_matches.append((global_y, col_start, col_end))
                pos += m.end()
        if self._search_matches:
            self._search_idx = 0
        self._update_search_label()

    def _search_next(self):
        if not self._search_matches:
            return
        self._search_idx = (self._search_idx + 1) % len(self._search_matches)
        self._scroll_to_match()
        self._update_search_label()
        self.update()

    def _search_prev(self):
        if not self._search_matches:
            return
        self._search_idx = (self._search_idx - 1) % len(self._search_matches)
        self._scroll_to_match()
        self._update_search_label()
        self.update()

    def _scroll_to_match(self):
        if self._search_idx < 0 or self._search_idx >= len(self._search_matches):
            return
        my, _, _ = self._search_matches[self._search_idx]
        total = self._total_visible_lines()
        vis = self._screen.lines if self._screen else 0
        max_scroll = max(0, total - vis)
        target_start = max(0, my - vis + 2)
        if self._search_bar:
            self._search_offset = max_scroll - target_start
            self._search_offset = max(0, min(max_scroll, self._search_offset))
            self._scrollbar.setValue(max_scroll - self._search_offset)
        self.update()

    def _is_in_match(self, global_y, col):
        for my, c1, c2 in self._search_matches:
            if my == global_y and c1 <= col < c2:
                return True
        return False

    def _is_current_match(self, global_y, col):
        if self._search_idx < 0 or self._search_idx >= len(self._search_matches):
            return False
        my, c1, c2 = self._search_matches[self._search_idx]
        return my == global_y and c1 <= col < c2

    def _update_search_label(self):
        if not self._search_bar:
            return
        total = len(self._search_matches)
        cur = self._search_idx + 1 if self._search_idx >= 0 else 0
        self._search_bar._label.setText(f"{cur}/{total}" if total else "0/0")

    def _log_start(self):
        if not self._session_name:
            return
        safe_name = "".join(c for c in self._session_name if c.isalnum() or c in " _-")
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested_name = f"{safe_name}_{ts}.log"
        default_dir = os.path.join(get_data_dir(), "logs", safe_name)
        os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, suggested_name)
        parent = self.window() if self.window() else self
        file_path, _ = QFileDialog.getSaveFileName(parent, tr("log.select_dir"), default_path, "Log Files (*.log)")
        if not file_path:
            return
        self._log_manager.start_file(file_path)
        self._process_output(f"\x1b[32m\u2139 {tr('log.started')}: {self._log_manager.log_dir}\x1b[0m\r\n")

    def _log_stop(self):
        self._log_manager.stop()
        self._process_output(f"\x1b[33m\u2139 {tr('log.stopped')}\x1b[0m\r\n")

    def _log_open_folder(self):
        log_dir = self._log_manager.log_dir
        if log_dir and os.path.isdir(log_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))
        else:
            self._process_output(f"\x1b[33m\u26a0 {tr('log.no_folder')}\x1b[0m\r\n")
