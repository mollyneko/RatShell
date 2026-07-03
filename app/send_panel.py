from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QFrame, QSpinBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect
from PySide6.QtGui import QFont, QFontMetrics, QPainter, QColor, QTextCursor, QKeyEvent
from .i18n import tr
from .logger import debug


class _LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def paintEvent(self, event):
        self._editor._draw_line_numbers(event)


class SendTextEdit(QPlainTextEdit):
    send_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(tr("send_panel.input_placeholder"))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #252639; color: #cdd6f4;
                border: none; font-size: 12px;
                font-family: "Cascadia Code", "Consolas", monospace;
                padding: 4px 0 4px 4px;
            }
        """)
        f = QFont("Cascadia Code", 12)
        f.setStyleHint(QFont.Monospace)
        self.setFont(f)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setTabStopDistance(32)
        self._line_number_area = _LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_width()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ControlModifier:
                self.send_requested.emit()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def _update_line_number_width(self):
        digits = len(str(max(1, self.blockCount())))
        w = 8 + self.fontMetrics().horizontalAdvance("9") * digits
        self.setViewportMargins(w, 0, 0, 0)

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self._line_number_area_width(), cr.height()))

    def _line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 8 + self.fontMetrics().horizontalAdvance("9") * digits

    def _draw_line_numbers(self, event):
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor("#1e1e2e"))
        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        fm = self.fontMetrics()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                num = str(block_num + 1)
                painter.setPen(QColor("#585b70"))
                painter.drawText(0, int(top), self._line_number_area.width() - 4, int(fm.height()),
                                 Qt.AlignRight, num)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_num += 1
        painter.end()


class SendPanel(QWidget):
    send_command = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setStyleSheet("background: transparent;")
        self._send_count = 0
        self._send_timer = QTimer(self)
        self._send_timer.setSingleShot(True)
        self._send_timer.timeout.connect(self._send_next)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        controls = QFrame()
        controls.setStyleSheet("background-color: #1e1e2e; border-top: 1px solid #313244;")
        controls.setFixedHeight(28)
        cl = QHBoxLayout(controls)
        cl.setContentsMargins(6, 0, 6, 0)
        cl.setSpacing(6)

        self._count_label = QLabel(tr("send_panel.count"))
        cl.addWidget(self._count_label)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 9999)
        self.count_spin.setValue(1)
        self.count_spin.setFixedWidth(60)
        self.count_spin.setStyleSheet("""
            QSpinBox {
                background: #252639; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 2px 4px; font-size: 11px;
            }
            QSpinBox:focus { border-color: #89b4fa; }
        """)
        cl.addWidget(self.count_spin)

        self._interval_label = QLabel(tr("send_panel.interval"))
        cl.addWidget(self._interval_label)
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(0.01, 60.0)
        self.interval_spin.setValue(1.0)
        self.interval_spin.setSingleStep(0.1)
        self.interval_spin.setFixedWidth(70)
        self.interval_spin.setSuffix("s")
        self.interval_spin.setStyleSheet("""
            QDoubleSpinBox {
                background: #252639; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 2px 4px; font-size: 11px;
            }
            QDoubleSpinBox:focus { border-color: #89b4fa; }
        """)
        cl.addWidget(self.interval_spin)

        cl.addStretch()

        self._status_label = QLabel()
        self._status_label.setStyleSheet("color: #6c7086; font-size: 11px; background: transparent;")
        cl.addWidget(self._status_label)

        layout.addWidget(controls)

        input_bar = QFrame()
        input_bar.setStyleSheet("background-color: #181825;")
        il = QHBoxLayout(input_bar)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(4)

        self.cmd_input = SendTextEdit()
        self.cmd_input.send_requested.connect(self._on_send)
        il.addWidget(self.cmd_input, 1)

        btn_col = QVBoxLayout()
        btn_col.setContentsMargins(0, 4, 6, 4)
        btn_col.setSpacing(4)

        self.send_btn = QPushButton("\u25b6 " + tr("send_panel.send"))
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 4px 16px; font-size: 12px; font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton:disabled { background-color: #45475a; color: #6c7086; }
        """)
        self.send_btn.clicked.connect(self._on_send)
        btn_col.addWidget(self.send_btn)

        self.stop_btn = QPushButton("\u25a0 " + tr("send_panel.stop"))
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8; color: #1e1e2e;
                border: none; border-radius: 6px;
                padding: 4px 16px; font-size: 12px; font-weight: bold;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self.stop_btn.clicked.connect(self._stop_send)
        self.stop_btn.hide()
        btn_col.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("\u2716 " + tr("send_panel.clear"))
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244; color: #6c7086;
                border: none; border-radius: 6px;
                padding: 4px 12px; font-size: 11px;
                min-height: 24px;
            }
            QPushButton:hover { background-color: #45475a; color: #cdd6f4; }
        """)
        self.clear_btn.clicked.connect(lambda: self.cmd_input.clear())
        btn_col.addWidget(self.clear_btn)

        btn_col.addStretch()
        il.addLayout(btn_col)

        layout.addWidget(input_bar, 1)

    def _on_send(self):
        debug("SendPanel._on_send")
        text = self.cmd_input.toPlainText()
        if not text.strip():
            return
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return
        count = self.count_spin.value()
        self._send_lines = lines * count
        self._send_index = 0
        self.send_btn.hide()
        self.stop_btn.show()
        self._status_label.setText(tr("send_panel.sending").format(len(self._send_lines)))
        self._send_next()

    def _send_next(self):
        debug("SendPanel._send_next")
        if self._send_index >= len(self._send_lines):
            self._finish_send()
            return
        self.send_command.emit(self._send_lines[self._send_index])
        self._send_index += 1
        remaining = len(self._send_lines) - self._send_index
        self._status_label.setText(tr("send_panel.sending").format(remaining))
        if remaining > 0:
            interval_ms = int(self.interval_spin.value() * 1000)
            self._send_timer.start(max(interval_ms, 10))
        else:
            self._finish_send()

    def _stop_send(self):
        debug("SendPanel._stop_send")
        self._send_timer.stop()
        self._finish_send()

    def _finish_send(self):
        debug("SendPanel._finish_send")
        self._send_timer.stop()
        self.stop_btn.hide()
        self.send_btn.show()
        self._status_label.setText("")
        self._send_lines = []

    def connect_keyboard(self, widget):
        widget.installEventFilter(self)

    def update_strings(self):
        debug("SendPanel.update_strings")
        self._count_label.setText(tr("send_panel.count"))
        self._interval_label.setText(tr("send_panel.interval"))
        self.cmd_input.setPlaceholderText(tr("send_panel.input_placeholder"))
        self.send_btn.setText("\u25b6 " + tr("send_panel.send"))
        self.stop_btn.setText("\u25a0 " + tr("send_panel.stop"))
        self.clear_btn.setText("\u2716 " + tr("send_panel.clear"))
