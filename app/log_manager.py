import os
import re
import datetime


_ANSI_RE = re.compile(r"\x1b\[[\d;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[^\[\]]")
_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _clean(text):
    text = _ANSI_RE.sub("", text)
    text = _CTRL_RE.sub("", text)
    text = text.replace("\r", "")
    return text


class LogManager:
    def __init__(self):
        self._file = None
        self._path = None
        self._buf = ""

    @property
    def is_active(self):
        return self._file is not None

    @property
    def log_dir(self):
        if self._path:
            return os.path.dirname(self._path)
        return None

    def start_file(self, file_path):
        self.stop()
        folder = os.path.dirname(file_path)
        os.makedirs(folder, exist_ok=True)
        self._path = file_path
        self._file = open(self._path, "w", encoding="utf-8")
        self._write_line(f"--- Log started at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---")

    def stop(self):
        if self._file:
            if self._buf.strip():
                self._flush_buf()
            self._write_line(f"--- Log ended at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} ---")
            self._file.flush()
            self._file.close()
            self._file = None
            self._buf = ""

    def write(self, text):
        if not self._file or not text:
            return
        text = _clean(text)
        if not text:
            return
        self._buf += text
        while "\n" in self._buf:
            idx = self._buf.index("\n")
            line = self._buf[:idx]
            self._buf = self._buf[idx + 1:]
            self._write_line(line)

    def _flush_buf(self):
        if self._buf:
            self._write_line(self._buf)
            self._buf = ""

    def _write_line(self, text):
        if self._file and text.strip():
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            self._file.write(f"[{ts}] {text}\n")
            self._file.flush()
