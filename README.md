# System Health Monitor

A Python command-line script for monitoring CPU usage, memory usage, disk usage, and running processes on Linux or Windows. It prints a health report to the console and can also write the report and any threshold alerts to a log file.

## Requirements

- Linux or Windows
- Python 3.9 or newer
- `psutil`

## Install in VS Code

1. Open this project folder in VS Code.
2. Install the Microsoft Python extension if prompted.
3. Open **Terminal → New Terminal**.
4. Create and activate a virtual environment, then install the dependency:

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

In VS Code, select the `.venv` interpreter when prompted (or use **Python: Select Interpreter** from the Command Palette).

## Run once

In the VS Code terminal on Windows:

```powershell
python .\system_health_monitor.py
```

On Linux:

```bash
python3 system_health_monitor.py
```

The default alert threshold is 80% for CPU, memory, and the system drive (`C:\` on Windows or `/` on Linux). The report includes total running process count and the five processes using the most CPU (with memory usage shown too). If a metric exceeds its threshold, an `ALERT` is printed to the console.

## Options

```bash
python3 system_health_monitor.py --help
python3 system_health_monitor.py --cpu-threshold 75 --memory-threshold 85 --disk-threshold 90 --disk-path /var --log-file health.log
python3 system_health_monitor.py --interval 60 --log-file health.log
```

Windows PowerShell example:

```powershell
python .\system_health_monitor.py --interval 60 --log-file health.log
```

`--interval` repeats the check every N seconds; without it, the script takes one snapshot and exits. Use Ctrl+C to stop repeated monitoring. Alerts and regular status reports are written to both the console and the optional log file.

## Assignment requirements covered

- Checks CPU usage, memory usage, disk space, and running processes.
- Compares CPU, memory, and disk usage with configurable thresholds (80% by default).
- Sends threshold alerts to the console and, when `--log-file` is supplied, to a log file.
- Supports one-time checks and repeated monitoring.