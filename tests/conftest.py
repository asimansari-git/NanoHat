"""
conftest.py — Global Safety Interceptor and Fixtures for NanoHat Test Suite.
Guarantees that NO automated test can ever invoke real system commands (bluetoothctl,
nmcli, systemctl, powerprofilesctl, rfkill, killall, etc.) on the host machine.
"""

import sys
import os
import pytest
from unittest.mock import MagicMock

# Hard allowlist of safe commands or blocked system binaries
DANGEROUS_SYSTEM_BINARIES = {
    "bluetoothctl",
    "nmcli",
    "systemctl",
    "powerprofilesctl",
    "rfkill",
    "pkexec",
    "sudo",
    "killall",
    "pkill",
    "reboot",
    "shutdown",
}

@pytest.fixture(autouse=True, scope="session")
def enforce_test_mode_env():
    """Sets NANOHAT_TEST_MODE=1 across the entire pytest session."""
    os.environ["NANOHAT_TEST_MODE"] = "1"
    yield
    os.environ.pop("NANOHAT_TEST_MODE", None)


@pytest.fixture(autouse=True)
def block_real_hardware_subprocess(monkeypatch):
    """
    Autouse fixture that intercepts subprocess.run and subprocess.Popen across ALL tests.
    If any code attempts to invoke a dangerous hardware/system binary without a mock,
    this interceptor blocks execution and returns a safe mock result.
    """
    import subprocess
    import shutil
    try:
        import runtime.functions as rf
    except ImportError:
        rf = None

    orig_run = subprocess.run
    orig_popen = subprocess.Popen

    def intercepted_run(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd:
            bin_name = os.path.basename(str(cmd[0]))
        elif isinstance(cmd, str):
            bin_name = os.path.basename(cmd.split()[0])
        else:
            bin_name = ""

        if bin_name in DANGEROUS_SYSTEM_BINARIES:
            # Block real execution and return safe dummy output
            cmd_str = " ".join(cmd) if isinstance(cmd, (list, tuple)) else str(cmd)
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_res.stderr = ""
            if "powerprofilesctl" in bin_name:
                mock_res.stdout = "balanced\n"
            elif "show" in cmd_str:
                mock_res.stdout = "Powered: yes\n"
            elif "radio" in cmd_str:
                mock_res.stdout = "enabled\n"
            elif "status" in cmd_str:
                mock_res.stdout = "Active: active (running)\n"
            else:
                mock_res.stdout = "OK\n"
            return mock_res

        return orig_run(cmd, *args, **kwargs)

    def intercepted_popen(cmd, *args, **kwargs):
        if isinstance(cmd, (list, tuple)) and cmd:
            bin_name = os.path.basename(str(cmd[0]))
        elif isinstance(cmd, str):
            bin_name = os.path.basename(cmd.split()[0])
        else:
            bin_name = ""

        if bin_name in DANGEROUS_SYSTEM_BINARIES or bin_name in {"calc", "firefox", "gnome-terminal"}:
            mock_proc = MagicMock()
            mock_proc.pid = 99999
            mock_proc.returncode = 0
            mock_proc.poll.return_value = 0
            mock_proc.communicate.return_value = (b"", b"")
            return mock_proc

        return orig_popen(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", intercepted_run)
    monkeypatch.setattr(subprocess, "Popen", intercepted_popen)

    if rf:
        monkeypatch.setattr(rf.subprocess, "run", intercepted_run)
        monkeypatch.setattr(rf.subprocess, "Popen", intercepted_popen)
