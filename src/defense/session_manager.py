"""
SSH Session Termination Module
Terminates compromised SSH sessions instantly upon threat confirmation.
"""

import subprocess
import shutil
import os


from typing import Optional


class SessionManager:
    def __init__(self):
        self.is_linux = shutil.which("pkill") is not None or shutil.which("loginctl") is not None

    def terminate_session(self, session_id: str, username: Optional[str] = None) -> bool:

        """
        Kills active SSH session by session ID or username.
        Execution latency target: < 20ms.
        """
        print(f"[!] AUTONOMOUS ACTION: Terminating compromised session: {session_id} (user: {username})")

        if not self.is_linux:
            print(f"[MOCK] Simulated session termination for {session_id}")
            return True

        # Extract PID if embedded in session_id (e.g. sess_username_1234)
        try:
            parts = session_id.split("_")
            if len(parts) >= 3 and parts[-1].isdigit():
                pid = int(parts[-1])
                os.kill(pid, 9)  # SIGKILL
                return True
        except (ProcessLookupError, PermissionError, ValueError):
            pass

        # Try loginctl or pkill
        try:
            if username:
                subprocess.run(["pkill", "-9", "-u", username, "-t", "pts"], check=False)
                return True
        except Exception as e:
            print(f"[-] Session kill error: {e}")

        return False
