import threading
import time
import serial
from .base_connection import BaseConnection
from ..logger import debug


class SerialConnection(BaseConnection):
    def __init__(self, config):
        debug("SerialConnection.__init__", config.get("port", ""))
        super().__init__(config)
        self._port = config["port"]
        self._baudrate = config.get("baudrate", 115200)
        self._bytesize = config.get("bytesize", 8)
        self._parity = config.get("parity", "N")
        self._stopbits = config.get("stopbits", 1)
        self._ser = None

    @property
    def display_name(self):
        return f"Serial: {self._port} ({self._baudrate} baud)"

    def start(self):
        debug(f"Serial connect {self._port} {self._baudrate}baud")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                          "O": serial.PARITY_ODD, "M": serial.PARITY_MARK,
                          "S": serial.PARITY_SPACE}
            stopbits_map = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
            bytesize_map = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}

            self._ser = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=bytesize_map.get(self._bytesize, serial.EIGHTBITS),
                parity=parity_map.get(self._parity, serial.PARITY_NONE),
                stopbits=stopbits_map.get(self._stopbits, serial.STOPBITS_ONE),
                timeout=0.1,
            )
            self._running = True
            self._emit_signal(self.connected)

            while self._running:
                if self._ser.in_waiting:
                    data = self._ser.read(self._ser.in_waiting)
                    try:
                        text = data.decode("utf-8", errors="replace")
                    except Exception:
                        text = data.decode("latin-1", errors="replace")
                    self._emit_output(text)
                else:
                    time.sleep(0.02)

        except serial.SerialException as e:
            debug(f"Serial SerialException: {e}")
            try:
                self.error_occurred.emit(str(e))
            except RuntimeError:
                pass
        except Exception as e:
            debug(f"Serial error: {e}")
        finally:
            self._running = False
            if self._ser and self._ser.is_open:
                try:
                    self._ser.close()
                except Exception:
                    pass
            try:
                self.disconnected.emit("Serial connection closed")
            except RuntimeError:
                pass

    def send(self, data):
        debug("SerialConnection.send", data[:80] if data else "")
        if self._ser and self._ser.is_open and self._running:
            try:
                self._ser.write(data.encode("utf-8"))
            except Exception as e:
                self.error_occurred.emit(f"Send error: {e}")

    def disconnect(self):
        debug("SerialConnection.disconnect")
        self._running = False
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass
