import unittest
from unittest.mock import patch, MagicMock
import os
import pytest
from runtime.tools import ALL_TOOLS
from runtime.router import route_tools
from runtime.functions import (
    system_health, power_profile, toggle_wifi, service_status, restart_service
)

TEST_RESULTS = []

def record_result(case_name, query, expected_tool, result, notes=""):
    TEST_RESULTS.append({
        "case": case_name,
        "query": query,
        "expected": expected_tool,
        "result": result,
        "notes": notes
    })

@pytest.fixture(scope="session", autouse=True)
def generate_report():
    yield
    os.makedirs("reports", exist_ok=True)
    with open("reports/complex_sysadmin_incident_report.md", "w") as f:
        f.write("# NanoHat v3.0.0 Stress Test Report: High-Pressure Sysadmin Incident Response & Emergency Triage\n\n")
        f.write("## Persona & Emergency Incident Triage Profile\n")
        f.write("- **Persona**: DevOps / Sysadmin under stress.\n")
        f.write("- **Characteristics**: Urgent, condensed queries, combining multiple diagnostic requests, testing latency and precision.\n")
        f.write("- **Objective**: Verify rapid triage routing across critical system components under pressure.\n\n")

        total = len(TEST_RESULTS)
        passed = sum(1 for r in TEST_RESULTS if r["result"] == "OK")
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        f.write("## Executive Summary\n")
        f.write(f"- **Total Cases**: {total}\n")
        f.write(f"- **Passed**: {passed}\n")
        f.write(f"- **Failed/XFailed**: {failed}\n")
        f.write(f"- **Pass Rate**: {pass_rate:.1f}%\n\n")

        f.write("## Detailed Case Matrix\n")
        f.write("| Case | Query | Expected Tool | Result | Notes |\n")
        f.write("|---|---|---|---|---|\n")
        for r in TEST_RESULTS:
            f.write(f"| {r['case']} | `{r['query']}` | {r['expected']} | {r['result']} | {r['notes']} |\n")

        f.write("\n## Latency & Triage Routing Precision Under Urgency\n")
        f.write("Testing ensures the router correctly identifies the highest priority diagnostic tool during stressful queries, even when combined with secondary requests.\n\n")

        f.write("## Recommended Hardening Patches\n")
        f.write("- Ensure shell pipe (`|`) and `sudo` executions are strictly denied and explicitly caught by router or execution engine.\n")
        f.write("- Improve regex patterns for edge-case hardware throttling queries.\n")

class TestComplexSysadminIncident(unittest.TestCase):

    def check_routing(self, query, expected_tools, case_name, notes=""):
        try:
            tools = route_tools(query, ALL_TOOLS)
            names = [t["function"]["name"] for t in tools]
            for ext in expected_tools:
                self.assertIn(ext, names, f"Query '{query}' failed to route to {ext}. Got {names}")
            record_result(case_name, query, ", ".join(expected_tools), "OK", notes)
        except Exception as e:
            record_result(case_name, query, ", ".join(expected_tools), "FAIL", str(e))
            raise

    # 1. System Health / Overheating scenarios
    def test_incident_01_overheat(self):
        self.check_routing("The laptop is burning hot and freezing, show me what is using CPU and RAM right now!", ["system_health"], "Incident 01 - Thermal Throttling")

    def test_incident_02_ram_swap(self):
        self.check_routing("System crawling, swap is probably full. What is the memory and cpu usage?", ["system_health"], "Incident 02 - OOM/Swap Check")

    def test_incident_03_thermal_slowdown(self):
        self.check_routing("Everything is super slow, is it thermal throttling? Check cpu", ["system_health"], "Incident 03 - General Slowdown")

    def test_incident_04_cpu_spike(self):
        self.check_routing("Fans spinning at 100%, check CPU load average immediately", ["system_health"], "Incident 04 - Fan/CPU Spike")

    def test_incident_05_battery_drain(self):
        self.check_routing("Battery draining incredibly fast, check health and cpu", ["system_health"], "Incident 05 - Battery Drain")

    # 2. Audio/Pipewire Failures
    def test_incident_06_audio_crash(self):
        self.check_routing("Audio failed mid-call, restart pipewire immediately", ["restart_service"], "Incident 06 - Audio Crash")

    def test_incident_07_no_sound(self):
        self.check_routing("No sound on the headset, check pipewire status", ["service_status"], "Incident 07 - Audio Status")

    def test_incident_08_restart_wireplumber(self):
        self.check_routing("Wireplumber is dead, restart it!", ["restart_service"], "Incident 08 - Wireplumber Restart")

    # 3. Network Interface Drops
    def test_incident_09_wifi_drop(self):
        self.check_routing("Network interface dropped, check wifi status and reconnect", ["toggle_wifi"], "Incident 09 - Wifi Drop")

    def test_incident_10_vpn_disconnect(self):
        self.check_routing("VPN disconnected because wifi dropped, check wifi", ["toggle_wifi"], "Incident 10 - Wifi Dependency")

    def test_incident_11_bluetooth_mouse(self):
        self.check_routing("Bluetooth mouse disconnected, check bluetooth", ["toggle_bluetooth"], "Incident 11 - Bluetooth Drop")

    def test_incident_12_restart_network(self):
        self.check_routing("Restart NetworkManager service, connection is completely stuck", ["restart_service"], "Incident 12 - NetworkManager Restart")

    # 4. Service Daemons / Docker
    def test_incident_13_docker_dead(self):
        self.check_routing("Is the docker daemon dead? Check systemctl status docker", ["service_status"], "Incident 13 - Docker Status")

    def test_incident_14_docker_restart(self):
        self.check_routing("Containers are unresponsive, restart docker daemon", ["restart_service"], "Incident 14 - Docker Restart")

    def test_incident_15_ollama_crash(self):
        self.check_routing("Local LLM timeout, restart ollama service", ["restart_service"], "Incident 15 - Ollama Restart")

    def test_incident_16_nginx_status(self):
        self.check_routing("Web server 502, check status of nginx", ["service_status"], "Incident 16 - Nginx Status")

    # 5. Power Profiles / Runaway Processes
    def test_incident_17_power_balance(self):
        self.check_routing("Kill runaway firefox process and switch power profile to balanced", ["power_profile"], "Incident 17 - Power/Process")

    def test_incident_18_power_saver(self):
        self.check_routing("Battery at 5%, switch to power saver mode now!", ["power_profile"], "Incident 18 - Emergency Power Saver")

    def test_incident_19_performance_mode(self):
        self.check_routing("Need to compile the kernel, set power profile to performance", ["power_profile"], "Incident 19 - Performance Need")

    # 6. Expected Failures (Pipelines & Root Execution)
    @unittest.expectedFailure
    def test_incident_20_pipeline_ps(self):
        self.check_routing("ps aux | grep docker", ["system_health"], "Incident 20 - Pipeline (XFAIL)")

    @unittest.expectedFailure
    def test_incident_21_sudo_kill(self):
        self.check_routing("sudo killall -9 firefox", ["system_health"], "Incident 21 - Sudo Execution (XFAIL)")

    @unittest.expectedFailure
    def test_incident_22_root_restart(self):
        self.check_routing("sudo systemctl restart gdm", ["system_health"], "Incident 22 - Sudo Restart (XFAIL)")

    @unittest.expectedFailure
    def test_incident_23_complex_pipe(self):
        self.check_routing("systemctl status docker | grep Active", ["service_status"], "Incident 23 - Complex Pipe (XFAIL)")

    @unittest.expectedFailure
    def test_incident_24_auth_bypass(self):
        self.check_routing("pkexec systemctl restart NetworkManager", ["system_health"], "Incident 24 - pkexec bypass (XFAIL)")

    # 7. Additional stress combinations (25 - 40)
    def test_incident_25_multi_service(self):
        self.check_routing("Check status of docker and restart ollama", ["service_status", "restart_service"], "Incident 25 - Multi Service")

    def test_incident_26_health_and_power(self):
        self.check_routing("Check CPU temp and set profile to power saver", ["system_health", "power_profile"], "Incident 26 - Health & Power")

    def test_incident_27_wifi_and_service(self):
        self.check_routing("Wifi down, restart service NetworkManager", ["restart_service"], "Incident 27 - Wifi & Service")

    def test_incident_28_audio_and_bluetooth(self):
        self.check_routing("Bluetooth headset no audio, check bluetooth status", ["toggle_bluetooth"], "Incident 28 - Audio & BT")

    def test_incident_29_cpu_and_docker(self):
        self.check_routing("CPU at 100%, is docker doing this? Check docker status", ["service_status"], "Incident 29 - CPU & Docker")

    def test_incident_30_ram_and_ollama(self):
        self.check_routing("OOM killer activated, check memory and restart ollama", ["system_health", "restart_service"], "Incident 30 - RAM & Ollama")

    def test_incident_31_power_and_compile(self):
        self.check_routing("Set performance profile, compile is taking too long", ["power_profile"], "Incident 31 - Power & Compile")

    def test_incident_32_urgent_status(self):
        self.check_routing("Is postgresql running???", ["service_status"], "Incident 32 - Urgent Status")

    def test_incident_33_urgent_restart(self):
        self.check_routing("RESTART NGINX NOW!", ["restart_service"], "Incident 33 - Urgent Restart")

    def test_incident_34_hardware_panic(self):
        self.check_routing("Screen flashing, GPU hot, check system health", ["system_health"], "Incident 34 - Hardware Panic")

    def test_incident_35_network_panic(self):
        self.check_routing("Can't ping gateway, check wifi", ["toggle_wifi"], "Incident 35 - Network Panic")

    def test_incident_36_service_panic(self):
        self.check_routing("Database crashed, status of mysql", ["service_status"], "Incident 36 - DB Panic")

    def test_incident_37_combo_diagnostic(self):
        self.check_routing("Check battery health and wifi status", ["system_health", "toggle_wifi"], "Incident 37 - Combo Diag")

    def test_incident_38_combo_fix(self):
        self.check_routing("Turn on wifi and restart service docker", ["toggle_wifi", "restart_service"], "Incident 38 - Combo Fix")

    def test_incident_39_extreme_stress(self):
        self.check_routing("EVERYTHING IS BROKEN, CPU 100%, RESTART DOCKER!", ["system_health", "restart_service"], "Incident 39 - Extreme Stress")

    def test_incident_40_gentle_stress(self):
        self.check_routing("System seems a bit sluggish, check memory usage", ["system_health"], "Incident 40 - Gentle Stress")
