"""
Autonomous Firewall & Network Isolation Module
Executes real-time network layer intervention (iptables / ufw) to isolate compromised SSH clients.
"""

import subprocess
import shutil
from typing import Optional


class FirewallManager:
    def __init__(self, backend: str = "iptables", chain: str = "INSIDER_DEFENSE"):
        self.backend = backend
        self.chain = chain
        self.is_linux = shutil.which("iptables") is not None or shutil.which("ufw") is not None
        self._init_chain()

    def _init_chain(self):
        if not self.is_linux:
            return

        if self.backend == "iptables":
            try:
                # Create custom chain if not exists
                subprocess.run(["iptables", "-N", self.chain], stderr=subprocess.DEVNULL)
                subprocess.run(["iptables", "-C", "INPUT", "-j", self.chain], stderr=subprocess.DEVNULL, check=True)
            except subprocess.CalledProcessError:
                subprocess.run(["iptables", "-I", "INPUT", "1", "-j", self.chain], check=False)

    def block_ip(self, ip_address: str) -> bool:
        """
        Instantly drops all inbound traffic from suspected attacker IP.
        Execution latency target: < 15ms.
        """
        if not ip_address or ip_address in ["127.0.0.1", "localhost", "::1"]:
            print(f"[!] Refusing to block loopback IP: {ip_address}")
            return False

        print(f"[!] AUTONOMOUS ACTION: Isolating attacker IP {ip_address} via {self.backend}...")

        if not self.is_linux:
            print(f"[MOCK] Simulated firewall block for IP: {ip_address}")
            return True

        try:
            if self.backend == "iptables":
                cmd = ["iptables", "-I", self.chain, "1", "-s", ip_address, "-j", "DROP"]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return res.returncode == 0
            elif self.backend == "ufw":
                cmd = ["ufw", "deny", "from", ip_address]
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return res.returncode == 0
        except Exception as e:
            print(f"[-] Firewall rule application failed: {e}")
            return False

        return False

    def unblock_ip(self, ip_address: str) -> bool:
        if not self.is_linux:
            return True
        try:
            if self.backend == "iptables":
                subprocess.run(["iptables", "-D", self.chain, "-s", ip_address, "-j", "DROP"], check=True)
                return True
        except Exception:
            return False
        return False
