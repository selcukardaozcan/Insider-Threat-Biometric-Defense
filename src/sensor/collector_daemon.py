"""
Collector Daemon
Receives keystroke timing events from C hooks via Unix Domain Socket (or local IPC)
and forwards them to the feature extraction queue.
"""

import os
import sys
import json
import socket
import select
from typing import Callable, Optional

DEFAULT_SOCKET_PATH = "/var/run/insider_sensor.sock"

class CollectorDaemon:
    def __init__(self, socket_path: str = DEFAULT_SOCKET_PATH):
        self.socket_path = socket_path
        self.sock: Optional[socket.socket] = None
        self.running = False

    def setup_socket(self):
        # Unix domain socket is supported on Linux/POSIX and modern Windows (AF_UNIX)
        if hasattr(socket, "AF_UNIX"):
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.sock.bind(self.socket_path)
            try:
                os.chmod(self.socket_path, 0o666)
            except Exception as e:
                print(f"[!] Could not set socket permissions: {e}")
            self.sock.setblocking(False)
        else:
            # Fallback for platforms without AF_UNIX
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind(("127.0.0.1", 9999))
            self.sock.setblocking(False)

    def listen(self, callback: Callable[[dict], None]):
        self.setup_socket()
        self.running = True
        print(f"[*] Sensor Daemon listening on {self.socket_path}")

        try:
            while self.running:
                readable, _, _ = select.select([self.sock], [], [], 0.1)
                for s in readable:
                    data, _ = s.recvfrom(2048)
                    try:
                        event = json.loads(data.decode("utf-8").strip())
                        callback(event)
                    except Exception as err:
                        print(f"[-] Malformed sensor packet: {err}")
        finally:
            self.close()

    def close(self):
        self.running = False
        if self.sock:
            self.sock.close()
        if hasattr(socket, "AF_UNIX") and os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except OSError:
                pass
