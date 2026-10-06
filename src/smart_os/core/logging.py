from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import re

SECRET_KEYS = re.compile(r"password|passwd|token|secret|serial|instance.?id|hardware.?id|device.?id|username", re.I)
SECRET_TEXT = re.compile(r"(?i)(password|passwd|token|secret)\s*[:=]\s*[^\s,;]+")

def redact(value):
    if isinstance(value, dict):
        return {k: "[redacted]" if SECRET_KEYS.search(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return SECRET_TEXT.sub(r"\1=[redacted]", value)
    return value

class Journal:
    def __init__(self, path: Path):
        self.path = path
    def record(self, operation: str, state: str, **details):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = {"time": datetime.now(timezone.utc).isoformat(), "operation": operation,
                 "state": state, "details": redact(details)}
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    def export(self, destination: Path):
        destination.write_text(self.path.read_text(encoding="utf-8") if self.path.exists() else "", encoding="utf-8")

def export_report(destination: Path, report: dict):
    destination.write_text(json.dumps(redact(report), indent=2, ensure_ascii=False), encoding="utf-8")
