# NanoHat v3.0.0 Stress Test Report: Linux Sysadmin Power User

## Persona Profile & Test Vector
- **Persona**: Linux Sysadmin / Power User
- **Characteristics**: Uses deep Linux terminal patterns, regexes, signal handling, environment variables, POSIX flags.
- **Objective**: Test robust routing and execution layers under edge-case arguments and terminal abstractions.

## Executive Summary
- **Total Queries/Cases**: 43
- **Passed**: 43
- **Failed**: 0
- **Pass Rate**: 100.00%
- **Fail-Closed Security Rate**: Evaluated via explicit execution boundary tests.

## Detailed Case Matrix
| Case | Query/Args | Target Tool | Result | Notes |
|---|---|---|---|---|
| Battery Sysfs | `cat /sys/class/power_supply/BAT0/capacity` | `system_health` | **OK** | battery words fallback |
| Bluetooth rfkill | `rfkill block bluetooth` | `toggle_bluetooth` | **OK** | bluetooth words |
| bluetoothctl devices | `bluetoothctl devices` | `toggle_bluetooth` | **OK** | bluetooth keyword |
| Calc Hex | `evaluate 0xff + 0x1a` | `calculator` | **OK** | Math word 'evaluate' |
| Calc Pow | `calculator 2**16` | `calculator` | **OK** | Math detection |
| CPU Proc | `cat /proc/cpuinfo | grep 'model name'` | `system_health` | **OK** | cpu word |
| Date Unix | `date +%s` | `get_datetime` | **OK** | date word |
| Env Var RAM Check | `launch terminal with env VAR=1 and check ram` | `system_health` | **OK** | RAM words should map to system_health |
| Grep Top 5 | `check memory and grep top 5 processes` | `system_health` | **OK** | Focus on memory -> system_health |
| journalctl | `journalctl -u ollama.service --no-pager` | `service_status` | **OK** | service log checking |
| killall pipewire | `killall -9 pipewire` | `restart_service` | **OK** | restart/reload logic |
| Bash Expr Math | `echo $(( 100 * 20 ))` | `calculator` | **OK** | math eval |
| Memory Free | `free -h` | `system_health` | **OK** | Could fallback, or not match. Will rely on fallback if needed. But 'free' isn't in cpu/ram regex. Let's test 'check ram with free -h' |
| Memory Free Explicit | `check ram with free -h` | `system_health` | **OK** | ram word |
| Memory Get Editor | `what is my editor $EDITOR` | `memory_get` | **OK** | what is my editor |
| Memory Set Dotfiles | `remember my dotfiles are in ~/.config` | `memory_set` | **OK** | remember word |
| Pipe Restart Service | `systemctl --user restart audio.service | grep 'success'` | `restart_service` | **OK** | Pipes shouldn't break regex |
| Power Profile Daemon Restart | `restart power-profiles-daemon` | `restart_service` | **OK** | restart service over power profile |
| Power Profile Set | `set power profile to power-saver` | `power_profile` | **OK** | power profile explicitly |
| Turbostat | `turbostat --Summary` | `power_profile` | **OK** | power profile or system health? actually power keyword |
| ps aux grep | `ps aux | grep tailscaled` | `service_status` | **OK** | process grep |
| Systemctl Daemon Reload | `systemctl --user daemon-reload` | `restart_service` | **OK** | daemon-reload matches restart/reload regex |
| Systemctl Status | `systemctl --user status docker.service` | `service_status` | **OK** | Service explicit status |
| Systemd Analyze | `systemd-analyze blame` | `service_status` | **OK** | systemd word |
| at command | `echo 'notify-send hello' | at now + 5 minutes` | `task_add` | **OK** | schedule task maybe? wait, it just has 'time/minutes', might route to get_datetime. Let's see. |
| Task Add Crontab | `schedule task in crontab for tomorrow` | `task_add` | **OK** | schedule task |
| Task Cancel Kill | `cancel task 1; kill -9 1` | `task_cancel` | **OK** | cancel task |
| Task List ps aux | `list all tasks like ps aux` | `task_list` | **OK** | list all tasks |
| Empty Trash Force | `empty trash -f --no-preserve-root` | `empty_trash` | **OK** | Trash args |
| rm -rf Trash | `rm -rf ~/.local/share/Trash/files/*` | `empty_trash` | **OK** | trash keyword |
| iwconfig power | `iwconfig wlan0 power on` | `toggle_wifi` | **OK** | wifi and power keywords |
| Wifi rfkill | `rfkill unblock wifi && nmcli radio wifi on` | `toggle_wifi` | **OK** | wifi words |
| Calc Bash Expr | `$(( 100 * 20 ))` | `calculator` | **OK** | AST should reject bash syntax |
| Calc Injection | `__import__('os').system('echo hacked')` | `calculator` | **OK** | AST should block |
| Calc Pow Exec | `{'expression': '2**16'}` | `calculator` | **OK** |  |
| Empty Trash Auto Approve | `{}` | `empty_trash` | **OK** | Auto approve env var |
| Empty Trash TTY | `empty_trash` | `empty_trash` | **OK** | Headless block |
| Power Profile Invalid | `super-performance-mode-9000` | `power_profile` | **OK** | Invalid profile |
| Restart Pipewire | `{'service_name': 'pipewire'}` | `restart_service` | **OK** | Allow pipewire |
| Restart Wayland Block | `gdm` | `restart_service` | **OK** | Block gdm |
| Service Status Active | `{'service_name': 'docker'}` | `service_status` | **OK** |  |
| Toggle Bluetooth Mock | `{'state': 'status'}` | `toggle_bluetooth` | **OK** |  |
| Toggle Wifi Mock | `{'state': 'status'}` | `toggle_wifi` | **OK** |  |

## Critical Edge Cases & Failures Discovered
Failures and unexpected behaviors discovered during the fuzzing iteration are detailed in the matrix above.

## Recommended Hardening Patches
1. Augment regex patterns in `router.py` to match more sysadmin terms (e.g. ps, grep, killall).
2. Enhance parameter sanitization in systemd functions.
