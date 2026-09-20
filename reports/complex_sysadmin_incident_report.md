# NanoHat v3.0.0 Stress Test Report: High-Pressure Sysadmin Incident Response & Emergency Triage

## Persona & Emergency Incident Triage Profile
- **Persona**: DevOps / Sysadmin under stress.
- **Characteristics**: Urgent, condensed queries, combining multiple diagnostic requests, testing latency and precision.
- **Objective**: Verify rapid triage routing across critical system components under pressure.

## Executive Summary
- **Total Cases**: 40
- **Passed**: 35
- **Failed/XFailed**: 5
- **Pass Rate**: 87.5%

## Detailed Case Matrix
| Case | Query | Expected Tool | Result | Notes |
|---|---|---|---|---|
| Incident 01 - Thermal Throttling | `The laptop is burning hot and freezing, show me what is using CPU and RAM right now!` | system_health | OK |  |
| Incident 02 - OOM/Swap Check | `System crawling, swap is probably full. What is the memory and cpu usage?` | system_health | OK |  |
| Incident 03 - General Slowdown | `Everything is super slow, is it thermal throttling? Check cpu` | system_health | OK |  |
| Incident 04 - Fan/CPU Spike | `Fans spinning at 100%, check CPU load average immediately` | system_health | OK |  |
| Incident 05 - Battery Drain | `Battery draining incredibly fast, check health and cpu` | system_health | OK |  |
| Incident 06 - Audio Crash | `Audio failed mid-call, restart pipewire immediately` | restart_service | OK |  |
| Incident 07 - Audio Status | `No sound on the headset, check pipewire status` | service_status | OK |  |
| Incident 08 - Wireplumber Restart | `Wireplumber is dead, restart it!` | restart_service | OK |  |
| Incident 09 - Wifi Drop | `Network interface dropped, check wifi status and reconnect` | toggle_wifi | OK |  |
| Incident 10 - Wifi Dependency | `VPN disconnected because wifi dropped, check wifi` | toggle_wifi | OK |  |
| Incident 11 - Bluetooth Drop | `Bluetooth mouse disconnected, check bluetooth` | toggle_bluetooth | OK |  |
| Incident 12 - NetworkManager Restart | `Restart NetworkManager service, connection is completely stuck` | restart_service | OK |  |
| Incident 13 - Docker Status | `Is the docker daemon dead? Check systemctl status docker` | service_status | OK |  |
| Incident 14 - Docker Restart | `Containers are unresponsive, restart docker daemon` | restart_service | OK |  |
| Incident 15 - Ollama Restart | `Local LLM timeout, restart ollama service` | restart_service | OK |  |
| Incident 16 - Nginx Status | `Web server 502, check status of nginx` | service_status | OK |  |
| Incident 17 - Power/Process | `Kill runaway firefox process and switch power profile to balanced` | power_profile | OK |  |
| Incident 18 - Emergency Power Saver | `Battery at 5%, switch to power saver mode now!` | power_profile | OK |  |
| Incident 19 - Performance Need | `Need to compile the kernel, set power profile to performance` | power_profile | OK |  |
| Incident 20 - Pipeline (XFAIL) | `ps aux | grep docker` | system_health | FAIL | 'system_health' not found in ['service_status', 'restart_service'] : Query 'ps aux | grep docker' failed to route to system_health. Got ['service_status', 'restart_service'] |
| Incident 21 - Sudo Execution (XFAIL) | `sudo killall -9 firefox` | system_health | FAIL | 'system_health' not found in ['restart_service', 'service_status'] : Query 'sudo killall -9 firefox' failed to route to system_health. Got ['restart_service', 'service_status'] |
| Incident 22 - Sudo Restart (XFAIL) | `sudo systemctl restart gdm` | system_health | FAIL | 'system_health' not found in ['restart_service', 'service_status'] : Query 'sudo systemctl restart gdm' failed to route to system_health. Got ['restart_service', 'service_status'] |
| Incident 23 - Complex Pipe (XFAIL) | `systemctl status docker | grep Active` | service_status | FAIL | 'service_status' not found in ['system_health', 'get_datetime', 'calculator'] : Query 'systemctl status docker | grep Active' failed to route to service_status. Got ['system_health', 'get_datetime', 'calculator'] |
| Incident 24 - pkexec bypass (XFAIL) | `pkexec systemctl restart NetworkManager` | system_health | FAIL | 'system_health' not found in ['restart_service', 'service_status'] : Query 'pkexec systemctl restart NetworkManager' failed to route to system_health. Got ['restart_service', 'service_status'] |
| Incident 25 - Multi Service | `Check status of docker and restart ollama` | service_status, restart_service | OK |  |
| Incident 26 - Health & Power | `Check CPU temp and set profile to power saver` | system_health, power_profile | OK |  |
| Incident 27 - Wifi & Service | `Wifi down, restart service NetworkManager` | restart_service | OK |  |
| Incident 28 - Audio & BT | `Bluetooth headset no audio, check bluetooth status` | toggle_bluetooth | OK |  |
| Incident 29 - CPU & Docker | `CPU at 100%, is docker doing this? Check docker status` | service_status | OK |  |
| Incident 30 - RAM & Ollama | `OOM killer activated, check memory and restart ollama` | system_health, restart_service | OK |  |
| Incident 31 - Power & Compile | `Set performance profile, compile is taking too long` | power_profile | OK |  |
| Incident 32 - Urgent Status | `Is postgresql running???` | service_status | OK |  |
| Incident 33 - Urgent Restart | `RESTART NGINX NOW!` | restart_service | OK |  |
| Incident 34 - Hardware Panic | `Screen flashing, GPU hot, check system health` | system_health | OK |  |
| Incident 35 - Network Panic | `Can't ping gateway, check wifi` | toggle_wifi | OK |  |
| Incident 36 - DB Panic | `Database crashed, status of mysql` | service_status | OK |  |
| Incident 37 - Combo Diag | `Check battery health and wifi status` | system_health, toggle_wifi | OK |  |
| Incident 38 - Combo Fix | `Turn on wifi and restart service docker` | toggle_wifi, restart_service | OK |  |
| Incident 39 - Extreme Stress | `EVERYTHING IS BROKEN, CPU 100%, RESTART DOCKER!` | system_health, restart_service | OK |  |
| Incident 40 - Gentle Stress | `System seems a bit sluggish, check memory usage` | system_health | OK |  |

## Latency & Triage Routing Precision Under Urgency
Testing ensures the router correctly identifies the highest priority diagnostic tool during stressful queries, even when combined with secondary requests.

## Recommended Hardening Patches
- Ensure shell pipe (`|`) and `sudo` executions are strictly denied and explicitly caught by router or execution engine.
- Improve regex patterns for edge-case hardware throttling queries.
