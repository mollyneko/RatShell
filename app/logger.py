import os
import sys
import traceback
from datetime import datetime


_ENABLED = os.environ.get("RATSHELL_DEBUG", "").lower() in ("1", "true", "yes")


def debug(*args):
    if not _ENABLED:
        return
    msg = " ".join(str(a) for a in args)
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] {msg}", file=sys.stderr)


def error(*args):
    msg = " ".join(str(a) for a in args)
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{ts}] ERROR: {msg}", file=sys.stderr)
    traceback.print_stack(file=sys.stderr)
