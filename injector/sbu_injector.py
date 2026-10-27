#!/usr/bin/env python3
"""Inject the SteamOS Better UI stylesheets into Steam's Game Mode client.

Steam's Game Mode UI is a set of CEF pages. With remote debugging enabled
(~/.steam/steam/.cef-enable-remote-debugging) they listen on 127.0.0.1:8080.
This script polls that port, and for every page we style it makes sure a
<style id="sbu-<name>"> tag with the current CSS is present. Steam rebuilds
its pages on restart or reload, so the loop re-injects whenever a style is
missing or outdated.

Standard library only: SteamOS and Bazzite ship Python but not pip packages.
"""

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time
import urllib.request
from pathlib import Path

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 8080

# theme/<folder> -> how to recognise the CEF page it belongs to.
TARGETS = {
    "main": lambda title: title == "Steam Big Picture Mode",
    "mainmenu": lambda title: title.startswith("MainMenu"),
    "quickaccess": lambda title: title.startswith("QuickAccess"),
}


def load_theme(theme_dir):
    """Return {folder: [(name, css), ...]} in file name order."""
    theme = {}
    for folder in TARGETS:
        files = sorted((theme_dir / folder).glob("*.css"))
        theme[folder] = [(f.stem, f.read_text()) for f in files]
    return theme


def list_pages():
    url = f"http://{DEBUG_HOST}:{DEBUG_PORT}/json"
    with urllib.request.urlopen(url, timeout=3) as resp:
        return json.load(resp)


class CdpSocket:
    """Minimal WebSocket client, enough for Runtime.evaluate round trips."""

    def __init__(self, ws_url):
        path = "/" + ws_url.split("/", 3)[3]
        self.sock = socket.create_connection((DEBUG_HOST, DEBUG_PORT), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall(
            (
                f"GET {path} HTTP/1.1\r\nHost: {DEBUG_HOST}:{DEBUG_PORT}\r\n"
                "Upgrade: websocket\r\nConnection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
            ).encode()
        )
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("handshake closed")
            head += chunk
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError(head.split(b"\r\n", 1)[0].decode(errors="replace"))
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()
        )
        if expected not in head:
            raise ConnectionError("bad Sec-WebSocket-Accept")
        self.buf = head.split(b"\r\n\r\n", 1)[1]
        self.next_id = 1

    def _recv_exact(self, n):
        while len(self.buf) < n:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise ConnectionError("socket closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send_text(self, text):
        payload = text.encode()
        header = bytearray([0x81])
        n = len(payload)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header += struct.pack(">H", n)
        else:
            header.append(0x80 | 127)
            header += struct.pack(">Q", n)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_message(self):
        data = b""
        while True:
            b0, b1 = self._recv_exact(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._recv_exact(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._recv_exact(8))[0]
            data += self._recv_exact(n)
            if b0 & 0x80:
                return data.decode()

    def evaluate(self, expression):
        msg_id = self.next_id
        self.next_id += 1
        self._send_text(json.dumps({
            "id": msg_id,
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True},
        }))
        while True:
            reply = json.loads(self._recv_message())
            if reply.get("id") == msg_id:
                return reply.get("result", {}).get("result", {}).get("value")

    def close(self):
        self.sock.close()


def sync_expression(styles, remove=False):
    """JS that adds/updates our <style> tags and drops stale sbu-* ones.

    Returns how many tags it changed, so the caller can log real work only."""
    wanted = {} if remove else {f"sbu-{name}": css for name, css in styles}
    return f"""(() => {{
  const wanted = {json.dumps(wanted)};
  let changed = 0;
  for (const el of document.querySelectorAll('style[id^="sbu-"]')) {{
    if (!(el.id in wanted)) {{ el.remove(); changed++; }}
  }}
  for (const [id, css] of Object.entries(wanted)) {{
    let el = document.getElementById(id);
    if (!el) {{ el = document.createElement('style'); el.id = id; document.head.appendChild(el); }}
    if (el.textContent !== css) {{ el.textContent = css; changed++; }}
  }}
  return changed;
}})()"""


def sync_once(theme, remove=False):
    """One pass over the open pages. Returns the number of pages touched."""
    touched = 0
    for page in list_pages():
        for folder, matches in TARGETS.items():
            if not matches(page.get("title", "")) or "webSocketDebuggerUrl" not in page:
                continue
            cdp = CdpSocket(page["webSocketDebuggerUrl"])
            try:
                changed = cdp.evaluate(sync_expression(theme[folder], remove))
            finally:
                cdp.close()
            if changed:
                touched += 1
                print(f"{'removed from' if remove else 'styled'} {page['title']} ({changed})", flush=True)
    return touched


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--theme", type=Path, default=here.parent / "theme")
    parser.add_argument("--once", action="store_true", help="inject once and exit")
    parser.add_argument("--remove", action="store_true", help="remove the styles and exit")
    parser.add_argument("--interval", type=float, default=2.0)
    args = parser.parse_args()

    if args.once or args.remove:
        try:
            sync_once(load_theme(args.theme), remove=args.remove)
        except OSError as exc:
            sys.exit(f"Steam debugger not reachable on {DEBUG_HOST}:{DEBUG_PORT}: {exc}")
        return

    while True:
        try:
            # Re-read the CSS every pass so edits apply without restarting.
            sync_once(load_theme(args.theme))
        except (OSError, ConnectionError, ValueError):
            pass  # Steam not up yet, or restarting: try again next pass.
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
