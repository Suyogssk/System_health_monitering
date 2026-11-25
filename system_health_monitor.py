#!/usr/bin/env python3
"""Monitor CPU, memory, disk, and processes; report threshold alerts."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil
except ImportError:
    print("Missing dependency: install it with 'python3 -m pip install -r requirements.txt'.", file=sys.stderr)
    raise SystemExit(2)


def configure_logging(log_file: str | None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def collect_metrics(disk_path: str, top_processes: int) -> dict[str, Any]:
    """Collect one health snapshot. CPU is sampled over a one-second interval."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(disk_path)
    processes = []
    for proc in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            processes.append({
                "pid": info["pid"],
                "name": info.get("name") or "?",
                "username": info.get("username") or "?",
                "cpu_percent": info.get("cpu_percent") or 0.0,
                "memory_percent": info.get("memory_percent") or 0.0,
                "status": info.get("status") or "?",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    processes.sort(key=lambda p: (p["cpu_percent"], p["memory_percent"]), reverse=True)
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_percent": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "process_count": len(processes),
        "top_processes": processes[:top_processes],
    }


def format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def report(metrics: dict[str, Any], args: argparse.Namespace) -> bool:
    logging.info("System health snapshot (UTC %s)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("CPU: %.1f%% (threshold %.1f%%)", metrics["cpu_percent"], args.cpu_threshold)
    logging.info(
        "Memory: %.1f%%, %s / %s (threshold %.1f%%)",
        metrics["memory_percent"], format_bytes(metrics["memory_used"]),
        format_bytes(metrics["memory_total"]), args.memory_threshold,
    )
    logging.info(
        "Disk %s: %.1f%%, %s / %s (threshold %.1f%%)",
        args.disk_path, metrics["disk_percent"], format_bytes(metrics["disk_used"]),
        format_bytes(metrics["disk_total"]), args.disk_threshold,
    )
    logging.info("Running processes: %d", metrics["process_count"])
    if metrics["top_processes"]:
        logging.info("Top processes by CPU / memory:")
        for proc in metrics["top_processes"]:
            logging.info(
                "  PID %-7s %-24.24s CPU %5.1f%% MEM %5.1f%% user=%s status=%s",
                proc["pid"], proc["name"], proc["cpu_percent"],
                proc["memory_percent"], proc["username"], proc["status"],
            )

    alerts = []
    for label, value, threshold in (
        ("CPU usage", metrics["cpu_percent"], args.cpu_threshold),
        ("Memory usage", metrics["memory_percent"], args.memory_threshold),
        ("Disk usage", metrics["disk_percent"], args.disk_threshold),
    ):
        if value > threshold:
            alerts.append(f"{label} is {value:.1f}% (threshold: {threshold:.1f}%)")
    if alerts:
        for alert in alerts:
            logging.warning("ALERT: %s", alert)
        return True
    logging.info("Status: OK (all metrics are within thresholds)")
    return False


def positive_interval(value: str) -> int:
    try:
        number = int(value)
        if number > 0:
            return number
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("interval must be a positive whole number of seconds")


def percentage(value: str) -> float:
    try:
        number = float(value)
        if 0 <= number <= 100:
            return number
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("threshold must be a number from 0 to 100")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu-threshold", type=percentage, default=80.0, help="CPU alert threshold %% (default: 80)")
    parser.add_argument("--memory-threshold", type=percentage, default=80.0, help="memory alert threshold %% (default: 80)")
    parser.add_argument("--disk-threshold", type=percentage, default=80.0, help="disk alert threshold %% (default: 80)")
    default_disk = (os.environ.get("SystemDrive", "C:") + "\\") if os.name == "nt" else "/"
    parser.add_argument("--disk-path", default=default_disk, help=f"filesystem mount/path to check (default: {default_disk})")
    parser.add_argument("--log-file", help="also write output and alerts to this log file")
    parser.add_argument("--interval", type=positive_interval, help="repeat every N seconds; omit for a single snapshot")
    parser.add_argument("--top-processes", type=int, default=5, help="number of busiest processes to show (default: 5)")
    args = parser.parse_args()
    if args.top_processes < 0:
        parser.error("--top-processes must be zero or greater")
    if not Path(args.disk_path).exists():
        parser.error(f"disk path does not exist: {args.disk_path}")
    return args


def main() -> int:
    args = parse_args()
    configure_logging(args.log_file)
    logging.info("Starting system health monitor")
    try:
        while True:
            report(collect_metrics(args.disk_path, args.top_processes), args)
            if args.interval is None:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logging.info("Monitor stopped")
    except (OSError, psutil.Error) as exc:
        logging.error("Could not collect system metrics: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())