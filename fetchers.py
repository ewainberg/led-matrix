from __future__ import annotations

import json
import re
from typing import Any, Optional

import requests

from state import ModeSnapshot, snap_ok, snap_err
from utils import sanitize_one_line


def _parse_json_or_jsonp(text: str) -> Optional[Any]:
    t = text.strip()

    try:
        return json.loads(t)
    except Exception:
        pass

    m = re.match(r"^[a-zA-Z_$][\w$]*\((.*)\)\s*;?\s*$", t, re.DOTALL)
    if not m:
        return None

    inner = m.group(1).strip()
    try:
        return json.loads(inner)
    except Exception:
        return None


class Fetcher:
    def __init__(
        self,
        weather_url: str,
        bus_url: str,
        excuses_url: str,
        message_url: str,
        next_url: str,
        timeout_s: int = 8,
    ) -> None:
        self.weather_url = weather_url
        self.bus_url = bus_url
        self.excuses_url = excuses_url
        self.message_url = message_url
        self.next_url = next_url
        self.timeout_s = timeout_s

    def fetch_weather(self) -> ModeSnapshot:
        try:
            r = requests.get(self.weather_url, timeout=self.timeout_s)
            if r.status_code != 200:
                return snap_err(f"Weather HTTP {r.status_code}")

            doc = r.json()
            temp_f = str(doc["current"]["temp_f"])
            condition = str(doc["current"]["condition"]["text"])
            text = sanitize_one_line(f"{condition}, {temp_f}F")

            return snap_ok(text, doc)

        except Exception as e:
            return snap_err(f"Weather error: {e.__class__.__name__}")

    def fetch_bus(self) -> ModeSnapshot:
        try:
            r = requests.get(self.bus_url, timeout=self.timeout_s)
            if r.status_code != 200:
                return snap_err(f"Bus HTTP {r.status_code}")

            doc = _parse_json_or_jsonp(r.text)
            if doc is None:
                return snap_err("Bus parse error")

            times = None
            if isinstance(doc, dict):
                times = doc.get("Times")
            elif isinstance(doc, list) and doc and isinstance(doc[0], dict):
                times = doc[0].get("Times")

            if not times:
                return snap_err("No times")

            msg = "Bus: "
            count = 0
            for t in times:
                if not isinstance(t, dict):
                    continue
                sec = t.get("Seconds", -1)
                if isinstance(sec, int) and sec > 0:
                    mins = max(1, sec // 60)
                    msg += f"{mins}m "
                    count += 1
                    if count >= 3:
                        break

            text = sanitize_one_line(msg) if count else "Bus times unavailable"
            return snap_ok(text, doc)

        except Exception as e:
            return snap_err(f"Bus error: {e.__class__.__name__}")

    def fetch_excuse(self) -> ModeSnapshot:
        try:
            r = requests.get(self.excuses_url, timeout=self.timeout_s)
            if r.status_code != 200:
                return snap_err(f"Excuse HTTP {r.status_code}")

            doc = r.json()
            txt = doc.get("text")
            if isinstance(txt, str) and txt:
                return snap_ok(sanitize_one_line("Excuse: " + txt), doc)

            return snap_err("Excuse parse error")

        except Exception as e:
            return snap_err(f"Excuse error: {e.__class__.__name__}")

    def fetch_message(self) -> ModeSnapshot:
        try:
            r = requests.get(self.message_url, timeout=self.timeout_s)
            if r.status_code != 200:
                return snap_err(f"Message HTTP {r.status_code}")

            msg = r.text.strip()
            if not msg or msg.lower() in ("no messages", "no message"):
                if self.next_url:
                    try:
                        requests.get(self.next_url, timeout=6)
                    except Exception:
                        pass
                return snap_ok("", {"message": "", "note": "empty"})

            msg_clean = sanitize_one_line(msg)

            if self.next_url:
                try:
                    requests.get(self.next_url, timeout=6)
                except Exception:
                    pass

            return snap_ok(msg_clean, {"message": msg_clean})

        except Exception as e:
            return snap_err(f"Message error: {e.__class__.__name__}")
