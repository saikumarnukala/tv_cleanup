#!/usr/bin/env python3
"""Interactive Wi-Fi Remote Control for Samsung Smart TVs (H-Series / Tizen).

Works over local Wi-Fi without needing the physical remote control.
Usage:
    python tools/samsung_remote.py
    python tools/samsung_remote.py KEY_VOLUP
    python tools/samsung_remote.py KEY_SOURCE
"""
import json
import os
import sys
import time

# Windows console encoding safeguard
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

try:
    import samsungctl
except ImportError:
    sys.exit("samsungctl is required. Run: pip install samsungctl websocket-client")

DEFAULT_IP = "192.168.31.130"
PORT = 8001

KEY_MAP = {
    "w": "KEY_UP",
    "x": "KEY_DOWN",
    "a": "KEY_LEFT",
    "d": "KEY_RIGHT",
    "s": "KEY_SOURCE",
    "p": "KEY_POWER",
    "1": "KEY_VOLUP",
    "+": "KEY_VOLUP",
    "2": "KEY_VOLDOWN",
    "-": "KEY_VOLDOWN",
    "3": "KEY_MUTE",
    "m": "KEY_MENU",
    "h": "KEY_HOME",
    "b": "KEY_RETURN",
    "i": "KEY_INFO",
    "ok": "KEY_ENTER",
    "enter": "KEY_ENTER",
}


def get_remote(ip: str):
    config = {
        "name": "AntigravityRemote",
        "description": "PC Remote",
        "id": "",
        "host": ip,
        "port": PORT,
        "method": "websocket",
        "timeout": 5,
    }
    return samsungctl.Remote(config)


def interactive_mode(remote, ip: str):
    print("======================================================")
    print(f"     Samsung Smart TV Wi-Fi Remote ({ip})           ")
    print("======================================================")
    print("  Navigation:                        Volume & Controls: ")
    print("   [W] Up                             [1 / +] Volume Up")
    print("   [A] Left   [D] Right               [2 / -] Volume Down")
    print("   [X] Down                           [3] Mute Toggle")
    print("   [Enter / Space] OK / Select        [S] Source / Input (HDMI)")
    print("   [B] Back / Return                  [M] TV Settings Menu")
    print("   [H] Smart Hub                      [P] Power Toggle")
    print("                                      [I] Info Banner")
    print("======================================================")
    print("Type key and press Enter (or enter full KEY_NAME). 'q' to exit.\n")

    while True:
        try:
            cmd = input("Samsung Remote > ").strip().lower()
            if not cmd:
                continue
            if cmd in ("q", "quit", "exit"):
                break

            target_key = KEY_MAP.get(cmd)
            if not target_key:
                if cmd.upper().startswith("KEY_"):
                    target_key = cmd.upper()
                else:
                    print(f"Unknown command: '{cmd}'. Use W/A/S/D/1/2/3/M/P or Q.")
                    continue

            remote.control(target_key)
            print(f"[OK] Sent: {target_key}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[!] Error sending key: {e}")
            try:
                remote = get_remote(ip)
            except Exception:
                pass

    print("Remote session closed.")


def main():
    args = sys.argv[1:]
    target_ip = DEFAULT_IP

    # Allow custom IP if provided as first arg
    if args and "." in args[0]:
        target_ip = args.pop(0)

    # Direct key execution mode
    if args:
        key_input = args[0]
        target_key = KEY_MAP.get(key_input.lower(), key_input)
        if not target_key.startswith("KEY_"):
            target_key = f"KEY_{target_key.upper()}"

        print(f"Connecting to Samsung TV at {target_ip}...")
        try:
            with get_remote(target_ip) as remote:
                remote.control(target_key)
                print(f"[OK] Successfully sent {target_key} to TV!")
        except Exception as e:
            print(f"[!] Failed to send {target_key}: {e}")
        return

    # Interactive remote mode
    print(f"Connecting to Samsung Smart TV at {target_ip}:8001...")
    try:
        remote = get_remote(target_ip)
        print(f"[OK] Connected to Samsung TV at {target_ip}!")
        interactive_mode(remote, target_ip)
        remote.close()
    except Exception as e:
        print(f"[!] Could not connect to Samsung TV at {target_ip}:8001: {e}")
        print("    Ensure the TV is powered ON and connected to Wi-Fi.")


if __name__ == "__main__":
    main()
