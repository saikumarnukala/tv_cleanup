#!/usr/bin/env python3
"""One-click maintenance and cache-trimming tool for connected Android & Fire TVs.

Usage:
    python tools/clean.py [tv_ip] [--close-adb]
    python tools/clean.py --all
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
PYTHON = sys.executable
TV_PY = TOOLS / "tv.py"
DEVICES_FILE = ROOT / ".local_devices.json"


def run_tv_cmd(host: str, cmd: str, timeout: int = 20) -> tuple[int, str]:
    """Execute an ADB shell command via tools/tv.py."""
    env = os.environ.copy()
    env["TV_HOST"] = host
    try:
        proc = subprocess.run(
            [PYTHON, str(TV_PY), cmd],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout.strip()
    except Exception as e:
        return 1, str(e)


def probe_device(host: str, timeout: int = 10) -> dict[str, str]:
    """Probe the TV for device model and Android version."""
    env = os.environ.copy()
    env["TV_HOST"] = host
    try:
        proc = subprocess.run(
            [PYTHON, str(TV_PY), "--probe"],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode != 0:
            return {}
        info = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()
        return info
    except Exception:
        return {}


def parse_free_mem(free_output: str) -> str:
    """Extract free memory in MB from free -m output."""
    for line in free_output.splitlines():
        if line.startswith("Mem:"):
            parts = line.split()
            if len(parts) >= 4:
                return f"{parts[3]} MB free"
    return "N/A"


def parse_free_disk(df_output: str) -> str:
    """Extract available disk storage from df -h /data."""
    lines = df_output.strip().splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 4:
            return f"{parts[3]} available ({parts[4]} used)"
    return "N/A"


def clean_tv(host: str, close_adb: bool = False) -> bool:
    """Run cache trimming and memory optimization on a single TV."""
    print(f"\n[+] Connecting to TV at {host}...")
    probe = probe_device(host)
    if not probe:
        print(f"[!] Could not connect to {host}:5555.")
        print("    Please verify:")
        print("    1. TV is turned ON and connected to the same Wi-Fi.")
        print("    2. ADB / USB Debugging is turned ON in Developer Options.")
        return False

    model = probe.get("ro.product.model", "Android TV")
    release = probe.get("ro.build.version.release", "Unknown")
    manufacturer = probe.get("ro.product.manufacturer", "")
    print(f"[✓] Connected: {manufacturer} {model} (Android {release})")

    # 1. Check initial memory and storage
    _, mem_before = run_tv_cmd(host, "free -m")
    _, disk_before = run_tv_cmd(host, "df -h /data")
    print(f"    Memory before:  {parse_free_mem(mem_before)}")
    print(f"    Storage before: {parse_free_disk(disk_before)}")

    # 2. Trim caches (2 GB threshold)
    print("    Trimming application caches...")
    code, _ = run_tv_cmd(host, "pm trim-caches 2000000000")
    if code != 0:
        print("    [!] Note: trim-caches returned non-zero, continuing...")

    # 3. Check updated memory and storage
    _, mem_after = run_tv_cmd(host, "free -m")
    _, disk_after = run_tv_cmd(host, "df -h /data")
    print(f"[✓] Cache trimmed successfully!")
    print(f"    Memory after:   {parse_free_mem(mem_after)}")
    print(f"    Storage after:  {parse_free_disk(disk_after)}")

    # 4. Optional ADB shutdown
    if close_adb:
        if "Amazon" in manufacturer or "AFT" in model:
            print("    Securing device: turning off ADB...")
            run_tv_cmd(host, "settings put global adb_enabled 0")
            print("    [✓] ADB disabled on Fire TV.")
        else:
            print("    [i] Reminder: Please disable USB Debugging in Developer Options on this TV.")

    return True


def load_saved_devices() -> dict[str, str]:
    """Load devices from local JSON config if present."""
    if DEVICES_FILE.exists():
        try:
            with open(DEVICES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main():
    if any(h in sys.argv for h in ("-h", "--help")):
        print((__doc__ or "").strip())
        return

    devices = load_saved_devices()
    close_adb = "--close-adb" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    # Direct IP supplied via CLI
    if args:
        target = args[0]
        clean_tv(target, close_adb=close_adb)
        return

    # All devices flag
    if "--all" in sys.argv and devices:
        for name, ip in devices.items():
            print(f"\n=== Cleaning {name} ({ip}) ===")
            clean_tv(ip, close_adb=close_adb)
        return

    # Interactive Menu
    print("======================================================")
    print("        Clean Your TV - One-Click Cache Cleaner       ")
    print("======================================================")

    device_list = list(devices.items())
    idx = 1
    for name, ip in device_list:
        print(f"  {idx}. {name} ({ip})")
        idx += 1

    if len(device_list) > 1:
        print(f"  {idx}. All saved TVs")
        all_opt = idx
        idx += 1
    else:
        all_opt = -1

    print(f"  {idx}. Enter custom TV IP address")
    custom_opt = idx
    print("======================================================")

    choice = input(f"Select an option (1-{idx}): ").strip()

    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(device_list):
            name, ip = device_list[choice_num - 1]
            clean_tv(ip, close_adb=close_adb)
        elif choice_num == all_opt:
            for name, ip in device_list:
                print(f"\n=== Cleaning {name} ({ip}) ===")
                clean_tv(ip, close_adb=close_adb)
        elif choice_num == custom_opt:
            custom_ip = input("Enter TV IP address (e.g. 192.168.1.50): ").strip()
            if custom_ip:
                clean_tv(custom_ip, close_adb=close_adb)
        else:
            print("[!] Invalid option selected.")
    except ValueError:
        print("[!] Invalid input.")


if __name__ == "__main__":
    main()
