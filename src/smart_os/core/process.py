from __future__ import annotations
import json
import os
import platform
import subprocess
from pathlib import Path

class UnsupportedPlatform(RuntimeError):
    pass

class OperationError(RuntimeError):
    pass

def run(argv: list[str], timeout: int = 90) -> str:
    """No shell interpolation; fail closed on exit status/timeout."""
    result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=timeout, shell=False,
                            creationflags=0x08000000 if os.name == "nt" else 0)
    if result.returncode:
        # Command output may contain device IDs or secrets. Keep it out of exceptions.
        raise OperationError(f"{Path(argv[0]).name} exited with code {result.returncode}")
    return result.stdout

def powershell(script: str, timeout: int = 90) -> str:
    if platform.system() != "Windows":
        raise UnsupportedPlatform("This operation requires Windows 10/11 x64")
    import base64
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    from .windows import system_executable
    executable = system_executable("powershell.exe")
    prefix = "$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
    encoded = base64.b64encode((prefix + script).encode("utf-16le")).decode("ascii")
    return run([executable, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], timeout)

def ps_literal(value: str) -> str:
    if "\x00" in value:
        raise ValueError("NUL in path")
    return "'" + value.replace("'", "''") + "'"

def json_rows(text: str) -> list[dict]:
    value = json.loads(text or "[]")
    return value if isinstance(value, list) else [value] if value else []
