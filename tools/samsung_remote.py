#!/usr/bin/env python3
"""Interactive Wi-Fi Remote Control for Samsung Smart TVs (H-Series / Tizen).

Works over local Wi-Fi without needing the physical remote control.
Usage:
    python tools/samsung_remote.py [TV_IP]
    python tools/samsung_remote.py KEY_VOLUP
    python tools/samsung_remote.py KEY_SOURCE
"""
import base64
import json
import os
import socket
import sys
import time

TV_IP = "192.168.31.130"
PORT = 8001


def make_websocket_frame(text: str) -> bytes:
    """Frame a text payload into a client-masked RFC 6455 WebSocket frame."""
    data = text.encode("utf-8")
    length = len(data)
    mask = b"\x12\x34\x56\x78"
    if length <= 125:
        header = bytes([0x81, 0x80 | length]) + mask
    elif length <= 65535:
        header = bytes([0x81, 0x80 | 126]) + length.to_bytes(2, "big") + mask
    else:
        header = bytes([0x81, 0x80 | 127]) + length.to_bytes(8, "big") + mask
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    return header + masked


class SamsungRemote:
    def __init__(self, ip: str = TV_IP):
        self.ip = ip
        self.sock = None

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(4.0)
            self.sock.connect((self.ip, PORT))

            app_name = base64.b64encode(b"AntigravityRemote").decode("ascii")
            req = (
                f"GET /api/v2/channels/samsung.remote.control?name={app_name} HTTP/1.1\r\n"
                f"Host: {self.ip}:{PORT}\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n"
                "Sec-WebSocket-Version: 13\r\n\r\n"
            )
            self.sock.sendall(req.encode("ascii"))
            resp = self.sock.recv(4096)
            if b"101 Switching Protocols" not in resp:
                print(f"[!] WebSocket upgrade rejected by {self.ip}: {resp[:100]}")
                return False

            # Wait for connection event
            self.sock.recv(4096)
            return True
        except Exception as e:
            print(f"[!] Connection failed: {e}")
            if self.sock:
                self.sock.close()
                self.sock = None
            return False

    def send_key(self, key_name: str) -> bool:
        if not self.sock:
            if not self.connect():
                return False
        payload = json.dumps({
            "method": "ms.remote.control",
            "params": {
                "Cmd": "Click",
                "DataOfCmd": key_name,
                "Option": "false",
                "TypeOfRemote": "SendRemoteKey",
            },
        })
        try:
            self.sock.sendall(make_websocket_frame(payload))
            return True
        except Exception:
            # Reconnect and retry once
            if self.connect():
                try:
                    self.sock.sendall(make_websocket_frame(payload))
                    return True
                except Exception:
                    pass
        return False

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


KEY_MAP = {
    "w": "KEY_UP",
    "x": "KEY_DOWN",
    "s": "KEY_SOURCE",
    "a": "KEY_LEFT",
    "d": "KEY_RIGHT",
    " ": "KEY_ENTER",
    "\r": "KEY_ENTER",
    "b": "KEY_RETURN",
    "m": "KEY_MENU",
    "h": "KEY_HOME",
    "p": "KEY_POWER",
    "1": "KEY_VOLUP",
    "2": "KEY_VOLDOWN",
    "3": "KEY_MUTE",
    "i": "KEY_INFO",
}


def interactive_mode(remote: SamsungRemote):
    print("======================================================")
    print("     Samsung Smart TV Wi-Fi Remote (UN32H5500)        ")
    print("======================================================")
    print("  Navigation:                        Volume & Controls: ")
    print("   [W] Up                             [1] Volume Up (+)")
    print("   [A] Left   [D] Right               [2] Volume Down (-)")
    print("   [X] Down                           [3] Mute Toggle")
    print("   [Enter / Space] OK / Select        [S] Source / Input (HDMI)")
    print("   [B] Back / Return                  [M] TV Settings Menu")
    print("   [H] Smart Hub                      [P] Power Toggle")
    print("                                      [I] Info Banner")
    print("======================================================")
    print("Type key and press Enter (or enter full KEY_NAME). 'q' to exit.")

    while True:
        try:
            cmd = input("TV Remote > ").strip().lower()
            if not cmd:
                continue
            if cmd in ("q", "quit", "exit"):
                break

            target_key = KEY_MAP.get(cmd)
            if not target_key:
                if cmd.upper().startswith("KEY_"):
                    target_key = cmd.upper()
                else:
                    print(f"Unknown command: '{cmd}'. Press W/A/S/D/1/2/3/M/P or Q.")
                    continue

            success = remote.send_key(target_key)
            if success:
                print(f"[OK] Sent: {target_key}")
            else:
                print(f"[!] Failed to send {target_key}")
        except (KeyboardInterrupt, EOFError):
            break

    remote.close()
    print("Remote session closed.")


def main():
    args = sys.argv[1:]
    target_ip = TV_IP

    # Check for custom IP
    if args and "." in args[0]:
        target_ip = args.pop(0)

    remote = SamsungRemote(target_ip)

    # Direct key execution mode
    if args:
        key = args[0]
        if not key.startswith("KEY_"):
            key = KEY_MAP.get(key.lower(), f"KEY_{key.upper()}")
        print(f"Sending {key} to Samsung TV at {target_ip}...")
        if remote.send_key(key):
            print("[OK] Success!")
        else:
            print("[!] Failed to send key.")
        remote.close()
        return

    # Interactive mode
    print(f"Connecting to Samsung Smart TV at {target_ip}:8001...")
    if not remote.connect():
        print(f"[!] Could not connect to Samsung TV at {target_ip}:8001.")
        print("    Ensure the TV is powered ON and connected to Wi-Fi.")
        return

    interactive_mode(remote)


if __name__ == "__main__":
    main()
