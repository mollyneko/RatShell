import threading
from PySide6.QtCore import QObject, Signal


class BaseConnection(QObject):
    output_received = Signal(str)
    connected = Signal()
    disconnected = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._running = False
        self._thread = None

    @property
    def display_name(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def send(self, data):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def _emit_output(self, text):
        try:
            self.output_received.emit(text)
        except RuntimeError:
            pass

    def _emit_signal(self, signal):
        try:
            signal.emit()
        except RuntimeError:
            pass
