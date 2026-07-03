import threading
import time
import socket
from .base_connection import BaseConnection
from ..logger import debug


class TelnetConnection(BaseConnection):
    def __init__(self, config):
        debug("TelnetConnection.__init__", config.get("host", ""))
        super().__init__(config)
        self._host = config["host"]
        self._port = config.get("port", 23)
        self._sock = None

    @property
    def display_name(self):
        return f"Telnet: {self._host}:{self._port}"

    def connect(self):
        debug(f"Telnet connect {self._host}:{self._port}")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(30)
            self._sock.connect((self._host, self._port))
            self._sock.setblocking(0)
            self._running = True
            self._emit_signal(self.connected)

            telnet_negotiation = False
            while self._running:
                try:
                    data = self._sock.recv(4096)
                    if data:
                        text = data.decode("utf-8", errors="replace")
                        self._emit_output(text)
                    else:
                        break
                except socket.timeout:
                    continue
                except BlockingIOError:
                    import random
                    time.sleep(0.02)
                except Exception as e:
                    try:
                        self.error_occurred.emit(str(e))
                    except RuntimeError:
                        pass
                    break

        except socket.timeout:
            debug("Telnet timeout")
            try:
                self.error_occurred.emit(f"Connection to {self._host}:{self._port} timed out")
            except RuntimeError:
                pass
        except ConnectionRefusedError:
            debug("Telnet connection refused")
            try:
                self.error_occurred.emit(f"Connection refused to {self._host}:{self._port}")
            except RuntimeError:
                pass
        except socket.gaierror:
            debug("Telnet DNS resolution failed")
            try:
                self.error_occurred.emit(f"Could not resolve hostname: {self._host}")
            except RuntimeError:
                pass
        except Exception as e:
            debug(f"Telnet error: {e}")
        finally:
            self._running = False
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
            try:
                self.disconnected.emit("Telnet session ended")
            except RuntimeError:
                pass

    def send(self, data):
        debug("TelnetConnection.send", data[:80] if data else "")
        if self._sock and self._running:
            try:
                self._sock.sendall(data.encode("utf-8"))
            except Exception as e:
                self.error_occurred.emit(f"Send error: {e}")

    def disconnect(self):
        debug("TelnetConnection.disconnect")
        self._running = False
        try:
            if self._sock:
                self._sock.close()
        except Exception:
            pass
