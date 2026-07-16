import threading
import paramiko
from .base_connection import BaseConnection
from ..logger import debug


class SSHConnection(BaseConnection):
    def __init__(self, config):
        debug("SSHConnection.__init__", config.get("host", ""))
        super().__init__(config)
        self._host = config["host"]
        self._port = config.get("port", 22)
        self._username = config.get("username", "")
        self._password = config.get("password", "")
        self._client = None
        self._channel = None
        self._recv_buf = ""

    @property
    def display_name(self):
        return f"SSH: {self._username}@{self._host}:{self._port}"

    def start(self):
        debug(f"SSH connect {self._username}@{self._host}:{self._port}")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                self._host,
                port=self._port,
                username=self._username if self._username else None,
                password=self._password if self._password else None,
                timeout=30,
                look_for_keys=False,
                allow_agent=False,
            )
            self._channel = self._client.invoke_shell(term="xterm-256color")
            self._channel.setblocking(0)
            self._running = True
            self._emit_signal(self.connected)

            while self._running:
                if self._channel.recv_ready():
                    data = self._channel.recv(4096)
                    if data:
                        try:
                            text = data.decode("utf-8", errors="replace")
                        except Exception:
                            text = data.decode("latin-1", errors="replace")
                        self._emit_output(text)
                elif self._channel.exit_status_ready():
                    break
                else:
                    import time
                    time.sleep(0.02)

        except Exception as e:
            debug(f"SSH error: {e}")
            try:
                self.error_occurred.emit(str(e))
            except RuntimeError:
                pass
        finally:
            self._running = False
            if self._client:
                self._client.close()
            try:
                self.disconnected.emit("SSH session ended")
            except RuntimeError:
                pass

    def send(self, data):
        debug("SSHConnection.send", data[:80] if data else "")
        if self._channel and self._running:
            try:
                self._channel.send(data.encode("utf-8"))
            except Exception as e:
                self.error_occurred.emit(f"Send error: {e}")

    def disconnect(self):
        debug("SSHConnection.disconnect")
        self._running = False
        try:
            if self._channel:
                self._channel.close()
            if self._client:
                self._client.close()
        except Exception:
            pass
