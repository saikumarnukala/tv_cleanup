#!/usr/bin/env python3
"""Wi-Fi Remote Control for Samsung Smart TV (H-Series / UN32H5500).

Uses encrypted WebSocket protocol with paired session token.
Usage:
    python tools/samsung_remote.py
    python tools/samsung_remote.py KEY_VOLUP
    python tools/samsung_remote.py KEY_SOURCE
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Windows console encoding safeguard
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / ".samsung_token.json"
DEFAULT_IP = "192.168.31.130"

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
    "tools": "KEY_TOOLS",
}


def load_token_data():
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return None


async def send_single_key(key_name: str, ip: str = DEFAULT_IP):
    import aiohttp
    from samsungtvws.encrypted.remote import SamsungTVEncryptedWSAsyncRemote, SendRemoteKey

    token_data = load_token_data()
    if not token_data:
        print("[!] No pairing token found. Run pairing first.")
        return False

    async with aiohttp.ClientSession() as session:
        remote = SamsungTVEncryptedWSAsyncRemote(
            token_data.get("ip", ip),
            web_session=session,
            token=token_data["token"],
            session_id=token_data["session_id"],
            port=8000,
            timeout=4.0,
        )
        try:
            await remote.start_listening()
            await remote.send_command(SendRemoteKey.click(key_name))
            await asyncio.sleep(0.3)
            await remote.close()
            return True
        except Exception as e:
            print(f"[!] Send error: {e}")
            return False


async def interactive_session(ip: str = DEFAULT_IP):
    import aiohttp
    from samsungtvws.encrypted.remote import SamsungTVEncryptedWSAsyncRemote, SendRemoteKey

    token_data = load_token_data()
    if not token_data:
        print("[!] No pairing token found. Run pairing first.")
        return

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

    async with aiohttp.ClientSession() as session:
        remote = SamsungTVEncryptedWSAsyncRemote(
            token_data.get("ip", ip),
            web_session=session,
            token=token_data["token"],
            session_id=token_data["session_id"],
            port=8000,
            timeout=4.0,
        )
        await remote.start_listening()
        print("[OK] Connected to Samsung TV! Ready for commands.\n")

        while True:
            try:
                cmd = await asyncio.get_event_loop().run_in_executor(None, lambda: input("Samsung Remote > ").strip().lower())
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

                await remote.send_command(SendRemoteKey.click(target_key))
                print(f"[OK] Sent: {target_key}")
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                print(f"[!] Error: {e}")

        await remote.close()
        print("Remote session closed.")


def main():
    args = sys.argv[1:]
    target_ip = DEFAULT_IP

    if args and "." in args[0]:
        target_ip = args.pop(0)

    # CLI direct key mode
    if args:
        raw_key = args[0]
        target_key = KEY_MAP.get(raw_key.lower(), raw_key)
        if not target_key.startswith("KEY_"):
            target_key = f"KEY_{target_key.upper()}"
        print(f"Sending {target_key} to Samsung TV at {target_ip}...")
        success = asyncio.run(send_single_key(target_key, target_ip))
        if success:
            print("[OK] Command executed on TV!")
        else:
            print("[!] Command failed.")
        return

    # Interactive mode
    asyncio.run(interactive_session(target_ip))


if __name__ == "__main__":
    main()
