from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QFormLayout, QCheckBox,
    QSpinBox, QMessageBox, QStackedWidget, QWidget, QSpacerItem,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .session_manager import list_sessions, load_session, save_session, default_session_data
from .i18n import tr
from .logger import debug


class ConnectionDialog(QDialog):
    connection_requested = Signal(dict)

    def __init__(self, parent=None, edit_data=None):
        super().__init__(parent)
        self._edit_data = edit_data
        is_edit = edit_data is not None
        self.setWindowTitle(tr("dialog.edit_session") if is_edit else tr("dialog.new_connection"))
        self.setFixedSize(540, 560)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._result = None

        self._build_ui(is_edit)
        self._setup_connections()
        if edit_data:
            self._fill_from_data(edit_data)

    def _build_ui(self, is_edit=False):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        container = QWidget()
        container.setObjectName("dialogContainer")
        container.setStyleSheet("""
            QWidget#dialogContainer {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 12px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setFixedHeight(44)
        title_bar.setStyleSheet("background: transparent;")
        tb_layout = QHBoxLayout(title_bar)
        tb_layout.setContentsMargins(16, 0, 8, 0)

        title_label = QLabel("\u26a1 " + (tr("dialog.edit_session") if is_edit else tr("dialog.new_connection")))
        title_label.setStyleSheet("color: #cdd6f4; font-size: 15px; font-weight: bold; background: transparent;")
        tb_layout.addWidget(title_label)
        tb_layout.addStretch()

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
        tb_layout.addWidget(close_btn)

        layout.addWidget(title_bar)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        form = QVBoxLayout(content)
        form.setContentsMargins(24, 8, 24, 24)
        form.setSpacing(12)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["SSH", "Serial", "Telnet"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 10px 14px; font-size: 13px;
                min-height: 20px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #cdd6f4;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                selection-background-color: #45475a;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
        """)
        form.addWidget(self.type_combo)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("dialog.display_name"))
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 10px 14px; font-size: 13px;
                min-height: 22px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
        """)
        form.addWidget(self.name_edit)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent;")

        self.stack.addWidget(self._ssh_form())
        self.stack.addWidget(self._serial_form())
        self.stack.addWidget(self._telnet_form())

        form.addWidget(self.stack)

        if not is_edit:
            quick_group = QGroupBox(tr("dialog.quick_actions"))
            quick_group.setStyleSheet("""
                QGroupBox {
                    color: #89b4fa; font-weight: bold;
                    border: 1px solid #45475a; border-radius: 8px;
                    margin-top: 8px; padding-top: 16px;
                    background: transparent;
                }
                QGroupBox::title {
                    subcontrol-origin: margin; left: 12px;
                    padding: 0 6px;
                }
            """)
            ql = QVBoxLayout(quick_group)
            ql.setContentsMargins(12, 20, 12, 12)
            sessions = list_sessions()
            self.session_combo = QComboBox()
            self.session_combo.addItem(tr("dialog.load_session"))
            for name, _ in sessions:
                self.session_combo.addItem(name)
            self.session_combo.setStyleSheet(self.type_combo.styleSheet())
            ql.addWidget(self.session_combo)
            self.save_cb = QCheckBox(tr("dialog.save_session"))
            self.save_cb.setStyleSheet("color: #a6adc8; spacing: 8px; background: transparent;")
            ql.addWidget(self.save_cb)
            form.addWidget(quick_group)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.cancel_btn = QPushButton(tr("dialog.cancel"))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 10px 24px; font-size: 13px;
            }
            QPushButton:hover { background-color: #45475a; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        btn_row.addStretch()

        self.connect_btn = QPushButton(tr("dialog.save") if is_edit else ("\u25b6 " + tr("dialog.connect")))
        self.connect_btn.setObjectName("accentBtn")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa; color: #1e1e2e;
                border: none; border-radius: 8px;
                padding: 10px 28px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_row.addWidget(self.connect_btn)

        form.addLayout(btn_row)

        layout.addWidget(content, 1)
        root.addWidget(container)

    def _ssh_form(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        f = QFormLayout(w)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(10)
        f.setLabelAlignment(Qt.AlignRight)

        self.ssh_host = QLineEdit()
        self.ssh_host.setPlaceholderText(tr("ssh.host_placeholder"))
        self.ssh_host.setMinimumHeight(36)
        f.addRow(self._label(tr("ssh.host")), self.ssh_host)

        host_port = QHBoxLayout()
        self.ssh_port = QLineEdit("22")
        self.ssh_port.setFixedWidth(80)
        self.ssh_port.setMinimumHeight(36)
        host_port.addWidget(self.ssh_port)
        host_port.addStretch()
        f.addRow(self._label(tr("ssh.port")), host_port)

        self.ssh_user = QLineEdit()
        self.ssh_user.setPlaceholderText(tr("ssh.username_placeholder"))
        self.ssh_user.setMinimumHeight(36)
        f.addRow(self._label(tr("ssh.username")), self.ssh_user)

        self.ssh_pass = QLineEdit()
        self.ssh_pass.setPlaceholderText(tr("ssh.password_placeholder"))
        self.ssh_pass.setEchoMode(QLineEdit.Password)
        self.ssh_pass.setMinimumHeight(36)
        f.addRow(self._label(tr("ssh.password")), self.ssh_pass)

        return w

    def _serial_form(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        f = QFormLayout(w)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(10)
        f.setLabelAlignment(Qt.AlignRight)

        port_row = QHBoxLayout()
        port_row.setSpacing(6)
        self.ser_port = QComboBox()
        self.ser_port.setEditable(True)
        self.ser_port.setMinimumHeight(36)
        self.ser_port.setStyleSheet("""
            QComboBox {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 8px;
                padding: 8px 14px; font-size: 13px;
                min-height: 22px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #cdd6f4;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px;
                selection-background-color: #45475a;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px; border-radius: 4px;
            }
        """)
        self._refresh_com_ports()
        port_row.addWidget(self.ser_port, 1)
        refresh_btn = QPushButton("\u21bb")
        refresh_btn.setFixedSize(36, 36)
        refresh_btn.setToolTip(tr("serial.refresh_ports"))
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #313244; color: #a6adc8;
                border: 1px solid #45475a; border-radius: 8px;
                font-size: 16px;
            }
            QPushButton:hover { background-color: #45475a; color: #cdd6f4; }
        """)
        refresh_btn.clicked.connect(self._refresh_com_ports)
        port_row.addWidget(refresh_btn)
        f.addRow(self._label(tr("serial.port")), port_row)

        self.ser_baud = QComboBox()
        self.ser_baud.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.ser_baud.setCurrentText("115200")
        self.ser_baud.setEditable(True)
        f.addRow(self._label(tr("serial.baud")), self.ser_baud)

        self.ser_bits = QComboBox()
        self.ser_bits.addItems(["5", "6", "7", "8"])
        self.ser_bits.setCurrentText("8")
        f.addRow(self._label(tr("serial.data_bits")), self.ser_bits)

        self.ser_parity = QComboBox()
        self.ser_parity.addItems(["None", "Even", "Odd", "Mark", "Space"])
        f.addRow(self._label(tr("serial.parity")), self.ser_parity)

        self.ser_stop = QComboBox()
        self.ser_stop.addItems(["1", "1.5", "2"])
        f.addRow(self._label(tr("serial.stop_bits")), self.ser_stop)

        return w

    def _telnet_form(self):
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        f = QFormLayout(w)
        f.setContentsMargins(0, 0, 0, 0)
        f.setSpacing(10)
        f.setLabelAlignment(Qt.AlignRight)

        self.tel_host = QLineEdit()
        self.tel_host.setPlaceholderText(tr("telnet.host_placeholder"))
        self.tel_host.setMinimumHeight(36)
        f.addRow(self._label(tr("telnet.host")), self.tel_host)

        self.tel_port = QLineEdit("23")
        self.tel_port.setFixedWidth(80)
        self.tel_port.setMinimumHeight(36)
        hp = QHBoxLayout()
        hp.addWidget(self.tel_port)
        hp.addStretch()
        f.addRow(self._label(tr("telnet.port")), hp)

        return w

    def _refresh_com_ports(self):
        self.ser_port.clear()
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for p in ports:
                label = f"{p.device}  ({p.description})" if p.description else p.device
                self.ser_port.addItem(label, p.device)
            if not ports:
                self.ser_port.addItem(tr("serial.no_ports_found"))
        except ImportError:
            self.ser_port.addItem("COM1")

    def _label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: 500; background: transparent;")
        lbl.setMinimumWidth(80)
        return lbl

    def _setup_connections(self):
        self.type_combo.currentIndexChanged.connect(self.stack.setCurrentIndex)
        if not self._edit_data:
            self.session_combo.currentIndexChanged.connect(self._on_session_selected)

    def _on_session_selected(self, idx):
        if idx <= 0:
            return
        name = self.session_combo.currentText()
        data = load_session(name)
        if data:
            self._fill_from_data(data)

    def _fill_from_data(self, data):
        tt = data.get("type", "ssh")
        type_idx = {"ssh": 0, "serial": 1, "telnet": 2}.get(tt, 0)
        self.type_combo.setCurrentIndex(type_idx)
        self.stack.setCurrentIndex(type_idx)
        self.name_edit.setText(data.get("display_name", ""))

        if tt == "ssh":
            self.ssh_host.setText(data.get("host", ""))
            self.ssh_port.setText(str(data.get("port", 22)))
            self.ssh_user.setText(data.get("username", ""))
            self.ssh_pass.setText(data.get("password", ""))
        elif tt == "serial":
            port = data.get("port", "COM1")
            idx = self.ser_port.findData(port)
            if idx >= 0:
                self.ser_port.setCurrentIndex(idx)
            else:
                self.ser_port.setCurrentText(port)
            self.ser_baud.setCurrentText(str(data.get("baudrate", 115200)))
            self.ser_bits.setCurrentText(str(data.get("bytesize", 8)))
            self.ser_parity.setCurrentText({"N": "None", "E": "Even", "O": "Odd", "M": "Mark", "S": "Space"}.get(
                data.get("parity", "N"), "None"))
            self.ser_stop.setCurrentText(str(data.get("stopbits", 1)))
        elif tt == "telnet":
            self.tel_host.setText(data.get("host", ""))
            self.tel_port.setText(str(data.get("port", 23)))

    def _on_connect(self):
        debug(f"_on_connect type={self.type_combo.currentText()} edit_mode={self._edit_data is not None}")
        tt = self.type_combo.currentText().lower()
        try:
            if tt == "ssh":
                host = self.ssh_host.text().strip()
                if not host:
                    raise ValueError(tr("error.host_required"))
                port = int(self.ssh_port.text().strip())
                data = {
                    "type": "ssh",
                    "host": host,
                    "port": port,
                    "username": self.ssh_user.text().strip(),
                    "password": self.ssh_pass.text().strip(),
                }
            elif tt == "serial":
                port_val = self.ser_port.currentData() or self.ser_port.currentText().strip()
                if not port_val or port_val == tr("serial.no_ports_found"):
                    raise ValueError(tr("error.serial_port_required"))
                data = {
                    "type": "serial",
                    "port": port_val,
                    "baudrate": int(self.ser_baud.currentText()),
                    "bytesize": int(self.ser_bits.currentText()),
                    "parity": {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}.get(
                        self.ser_parity.currentText(), "N"),
                    "stopbits": float(self.ser_stop.currentText()),
                }
            else:
                host = self.tel_host.text().strip()
                if not host:
                    raise ValueError(tr("error.host_required"))
                port = int(self.tel_port.text().strip())
                data = {"type": "telnet", "host": host, "port": port}

            name = self.name_edit.text().strip()
            if name:
                data["display_name"] = name

            if not self._edit_data and self.save_cb.isChecked():
                save_session(data.get("display_name") or data.get("host", data.get("port", "session")), data)

            self._result = data
            if not self._edit_data:
                self.connection_requested.emit(data)
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))

    @staticmethod
    def get_connection(parent=None):
        dlg = ConnectionDialog(parent)
        dlg.exec()
        return dlg._result
