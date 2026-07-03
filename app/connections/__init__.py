from .ssh_connection import SSHConnection
from .serial_connection import SerialConnection
from .telnet_connection import TelnetConnection


def create_connection(config):
    ct = config.get("type", "ssh")
    if ct == "ssh":
        return SSHConnection(config)
    elif ct == "serial":
        return SerialConnection(config)
    elif ct == "telnet":
        return TelnetConnection(config)
    else:
        raise ValueError(f"Unknown connection type: {ct}")
