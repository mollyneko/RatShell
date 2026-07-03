from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PySide6.QtCore import Qt, Signal, QPoint, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QBrush, QPen
from .i18n import tr
from .logger import debug


class WindowButton(QPushButton):
    def __init__(self, icon_text, color_hover, parent=None):
        super().__init__(parent)
        self._icon_text = icon_text
        self._color_hover = color_hover
        self._hovered = False
        self.setFixedSize(38, 28)
        self.setCursor(Qt.PointingHandCursor)

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if self._hovered:
            painter.fillRect(self.rect(), QColor(self._color_hover))

        painter.setPen(Qt.white if self._hovered else QColor("#cdd6f4"))
        f = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(f)
        painter.drawText(self.rect(), Qt.AlignCenter, self._icon_text)


class TitleBar(QWidget):
    MINIMIZE = "\u2500"
    MAXIMIZE = "\u25a1"
    CLOSE = "\u2715"

    def __init__(self, parent=None):
        debug("TitleBar.__init__")
        super().__init__(parent)
        self._parent = parent
        self._drag_pos = None
        self.setFixedHeight(30)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.icon_label = QLabel("\u25b6")
        self.icon_label.setStyleSheet("color: #89b4fa; font-size: 12px; padding: 0 8px;")
        self.icon_label.setFixedWidth(24)
        layout.addWidget(self.icon_label)

        self.title_label = QLabel(tr("title_bar.title"))
        self.title_label.setStyleSheet("color: #cdd6f4; font-size: 11px; font-weight: 600; background: transparent;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.title_label, 1)

        self.min_btn = WindowButton(self.MINIMIZE, "#585b70")
        self.min_btn.clicked.connect(self._on_minimize)
        layout.addWidget(self.min_btn)

        self.max_btn = WindowButton(self.MAXIMIZE, "#585b70")
        self.max_btn.clicked.connect(self._on_maximize)
        layout.addWidget(self.max_btn)

        self.close_btn = WindowButton(self.CLOSE, "#f38ba8")
        self.close_btn.clicked.connect(self._on_close)
        layout.addWidget(self.close_btn)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor("#1e1e2e"))
        gradient.setColorAt(0.5, QColor("#252639"))
        gradient.setColorAt(1.0, QColor("#1e1e2e"))
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.setPen(QPen(QColor("#313244"), 1))
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)

    def mousePressEvent(self, event):
        debug("TitleBar.mousePressEvent", event.pos())
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        debug("TitleBar.mouseMoveEvent", event.pos())
        if self._drag_pos is not None and self._parent:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self._parent.move(self._parent.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        debug("TitleBar.mouseDoubleClickEvent")
        self._on_maximize()

    def set_title(self, text):
        self.title_label.setText(text)

    def _on_minimize(self):
        debug("TitleBar._on_minimize")
        if self._parent:
            self._parent.setWindowState(Qt.WindowMinimized)

    def _on_maximize(self):
        debug("TitleBar._on_maximize")
        if self._parent:
            state = self._parent.windowState()
            if state & Qt.WindowMaximized:
                self._parent.setWindowState(Qt.WindowNoState)
            else:
                self._parent.setWindowState(Qt.WindowMaximized)

    def _on_close(self):
        debug("TitleBar._on_close")
        if self._parent:
            self._parent.close()
