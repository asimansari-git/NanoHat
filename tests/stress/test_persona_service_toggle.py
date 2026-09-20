import pytest
from unittest.mock import patch, MagicMock
import subprocess
from runtime.functions import toggle_wifi, toggle_bluetooth, restart_service

# --- toggle_wifi tests ---

@patch("runtime.functions.shutil.which", return_value=None)
def test_wifi_missing_binary(mock_which):
    assert "not found" in toggle_wifi("on")

@pytest.mark.parametrize("target", ["status", "check", "get", "STATUS", " Check "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_status_enabled(mock_which, mock_run, target):
    mock_proc = MagicMock()
    mock_proc.stdout = "enabled\n"
    mock_run.return_value = mock_proc

    res = toggle_wifi(target)
    assert "Yes, Wi-Fi radio is enabled." in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_status_disabled(mock_which, mock_run):
    mock_proc = MagicMock()
    mock_proc.stdout = "disabled\n"
    mock_run.return_value = mock_proc

    res = toggle_wifi("status")
    assert "No, Wi-Fi radio is disabled." in res

@pytest.mark.parametrize("target", ["on", "enable", "enabled", "ON", " Enable "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_on(mock_which, mock_run, target):
    res = toggle_wifi(target)
    assert "Wi-Fi radio turned on." in res
    mock_run.assert_called_with(["/usr/bin/nmcli", "radio", "wifi", "on"], capture_output=True, text=True, check=True)

@pytest.mark.parametrize("target", ["off", "disable", "disabled", "OFF", " Disable "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_off(mock_which, mock_run, target):
    res = toggle_wifi(target)
    assert "Wi-Fi radio turned off." in res
    mock_run.assert_called_with(["/usr/bin/nmcli", "radio", "wifi", "off"], capture_output=True, text=True, check=True)

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_toggle_from_enabled(mock_which, mock_run):
    def side_effect(*args, **kwargs):
        if "radio" in args[0] and len(args[0]) == 3:
            mock = MagicMock()
            mock.stdout = "enabled"
            return mock
        elif len(args[0]) == 4:
            return MagicMock()

    mock_run.side_effect = side_effect
    res = toggle_wifi("toggle")
    assert "Wi-Fi toggled from enabled to off." in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_toggle_from_disabled(mock_which, mock_run):
    def side_effect(*args, **kwargs):
        if "radio" in args[0] and len(args[0]) == 3:
            mock = MagicMock()
            mock.stdout = "disabled"
            return mock
        elif len(args[0]) == 4:
            return MagicMock()

    mock_run.side_effect = side_effect
    res = toggle_wifi("toggle")
    assert "Wi-Fi toggled from disabled to on." in res

@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_unknown_action(mock_which):
    res = toggle_wifi("jump")
    assert "Unsupported Wi-Fi action 'jump'" in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_wifi_rfkill_blocked_error(mock_which, mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "nmcli", stderr="Error: rfkill blocked")

    with pytest.raises(subprocess.CalledProcessError):
        toggle_wifi("on")

# --- toggle_bluetooth tests ---

@patch("runtime.functions.shutil.which", return_value=None)
def test_bluetooth_missing_binary(mock_which):
    assert "not found" in toggle_bluetooth("on")

@pytest.mark.parametrize("target", ["status", "check", "get", "STATUS", " Check "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_status_enabled(mock_which, mock_run, target):
    mock_proc = MagicMock()
    mock_proc.stdout = "Powered: yes\n"
    mock_run.return_value = mock_proc

    res = toggle_bluetooth(target)
    assert "Yes, Bluetooth is powered on." in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_status_disabled(mock_which, mock_run):
    mock_proc = MagicMock()
    mock_proc.stdout = "Powered: no\n"
    mock_run.return_value = mock_proc

    res = toggle_bluetooth("status")
    assert "No, Bluetooth is powered off." in res

@pytest.mark.parametrize("target", ["on", "enable", "enabled", "ON", " Enable "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_on(mock_which, mock_run, target):
    res = toggle_bluetooth(target)
    assert "Bluetooth powered on." in res
    mock_run.assert_called_with(["/usr/bin/bluetoothctl", "power", "on"], capture_output=True, text=True, check=True)

@pytest.mark.parametrize("target", ["off", "disable", "disabled", "OFF", " Disable "])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_off(mock_which, mock_run, target):
    res = toggle_bluetooth(target)
    assert "Bluetooth powered off." in res
    mock_run.assert_called_with(["/usr/bin/bluetoothctl", "power", "off"], capture_output=True, text=True, check=True)

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_toggle_from_enabled(mock_which, mock_run):
    def side_effect(*args, **kwargs):
        if "show" in args[0]:
            mock = MagicMock()
            mock.stdout = "Powered: yes"
            return mock
        elif "power" in args[0]:
            return MagicMock()

    mock_run.side_effect = side_effect
    res = toggle_bluetooth("toggle")
    assert "Bluetooth toggled from on to off." in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_toggle_from_disabled(mock_which, mock_run):
    def side_effect(*args, **kwargs):
        if "show" in args[0]:
            mock = MagicMock()
            mock.stdout = "Powered: no"
            return mock
        elif "power" in args[0]:
            return MagicMock()

    mock_run.side_effect = side_effect
    res = toggle_bluetooth("toggle")
    assert "Bluetooth toggled from off to on." in res

@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_unknown_action(mock_which):
    res = toggle_bluetooth("jump")
    assert "Unsupported Bluetooth action 'jump'" in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_bluetooth_command_error(mock_which, mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "bluetoothctl", stderr="org.bluez.Error.Failed")

    with pytest.raises(subprocess.CalledProcessError):
        toggle_bluetooth("on")

# --- restart_service tests ---

@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_empty(mock_which):
    res = restart_service("")
    assert "Error: Please specify the service name to restart" in res

@patch("runtime.functions.shutil.which", return_value=None)
def test_restart_service_missing_binary(mock_which):
    res = restart_service("pipewire")
    assert "not found" in res

@pytest.mark.parametrize("service", [
    "org.gnome.shell@wayland",
    "gdm",
    "gdm.service",
    "wayland",
    "Wayland",
    "GDM.SERVICE"
])
@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_blocked_wayland(mock_which, service):
    res = restart_service(service)
    assert "ERROR[security_blocked]" in res
    assert "strictly blocked" in res

@pytest.mark.parametrize("service", [
    "unknown_service",
    "fake_service.service",
    "nginx",
    "docker.service"
])
@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_not_allowlisted(mock_which, service):
    res = restart_service(service)
    assert "ERROR[security_blocked]" in res
    assert "not in the safe allowlist" in res

@pytest.mark.parametrize("service", [
    "pipewire",
    "pipewire.service",
    "wireplumber",
    "wireplumber.service",
    "xdg-desktop-portal",
    "xdg-desktop-portal-gnome"
])
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_success(mock_which, mock_run, service):
    res = restart_service(service)
    expected_unit = service if "." in service else f"{service}.service"
    assert f"Service '{expected_unit}' restarted successfully." in res
    mock_run.assert_called_with(["/usr/bin/systemctl", "--user", "restart", expected_unit.lower()], capture_output=True, text=True, check=True)

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_systemd_failure(mock_which, mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl", stderr="Failed to restart pipewire.service: Unit pipewire.service not found.")

    res = restart_service("pipewire")
    assert "Error restarting service 'pipewire.service'" in res
    assert "Failed to restart pipewire.service" in res

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/systemctl")
def test_restart_service_systemd_failure_no_stderr(mock_which, mock_run):
    mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl", stderr="")

    res = restart_service("pipewire")
    assert "Error restarting service 'pipewire.service'" in res
    assert "Command 'systemctl'" in res

# --- additional stress tests ---

@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_rapid_alternation_mocked(mock_which, mock_run):
    states = ["enabled", "disabled", "enabled", "disabled"]

    def side_effect(*args, **kwargs):
        if "radio" in args[0] and len(args[0]) == 3:
            mock = MagicMock()
            mock.stdout = states.pop(0)
            return mock
        return MagicMock()

    mock_run.side_effect = side_effect

    assert "Wi-Fi toggled from enabled to off." in toggle_wifi("toggle")
    assert "Wi-Fi toggled from disabled to on." in toggle_wifi("toggle")
    assert "Wi-Fi toggled from enabled to off." in toggle_wifi("toggle")
    assert "Wi-Fi toggled from disabled to on." in toggle_wifi("toggle")

@pytest.mark.parametrize("i", range(10))
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/nmcli")
def test_stress_idempotent_on(mock_which, mock_run, i):
    assert "Wi-Fi radio turned on." in toggle_wifi("on")
    assert mock_run.call_count == 1

@pytest.mark.parametrize("i", range(10))
@patch("runtime.functions.subprocess.run")
@patch("runtime.functions.shutil.which", return_value="/usr/bin/bluetoothctl")
def test_stress_idempotent_off(mock_which, mock_run, i):
    assert "Bluetooth powered off." in toggle_bluetooth("off")
    assert mock_run.call_count == 1
