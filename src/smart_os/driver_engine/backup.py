from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from ..core.process import run, powershell, ps_literal, UnsupportedPlatform
from ..core.integrity import sha256
from .matching import parse_inf, rank

class DriverSafetyError(ValueError):
    pass

def pnputil() -> str:
    if platform.system() != "Windows":
        raise UnsupportedPlatform("Driver Store operations require Windows")
    from ..core.windows import system_executable
    return system_executable("pnputil.exe")

def backup(destination: Path, inf: str = "*") -> dict:
    if inf != "*" and not re.fullmatch(r"oem[0-9]+\.inf", inf, re.I):
        raise DriverSafetyError("Only published OEM INF names can be exported")
    if destination.exists():
        raise DriverSafetyError("Choose a new empty backup destination")
    executable = pnputil()
    destination.mkdir(parents=True)
    try:
        run([executable, "/export-driver", inf, str(destination.resolve())], timeout=300)
        files = {}
        for file in destination.rglob("*"):
            if file.is_file():
                files[file.relative_to(destination).as_posix()] = sha256(file)
        if not any(name.lower().endswith(".inf") for name in files):
            raise DriverSafetyError("No third-party drivers exported; inbox Microsoft drivers are not included")
        manifest = {"schema_version": 1, "kind": "smart-driver-backup", "files": files,
                    "note": "Third-party drivers only. Hashes detect corruption, not publisher authenticity"}
        (destination / "smart-driver-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return {"packages": sum(name.lower().endswith(".inf") for name in files), "files": len(files)}
    except Exception:
        # Keep a partial export for diagnosis. Never label it a valid backup.
        raise

def verify_backup(directory: Path):
    directory = directory.resolve(strict=True)
    manifest = json.loads((directory / "smart-driver-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "smart-driver-backup" or not manifest.get("files"):
        raise DriverSafetyError("Unsupported or empty backup manifest")
    files = []
    for relative, expected in manifest["files"].items():
        if not isinstance(relative, str) or Path(relative).is_absolute() or any(x in relative for x in ["\\", ":"]):
            raise DriverSafetyError("Unsafe backup path")
        path = (directory / relative).resolve(strict=True)
        if not path.is_relative_to(directory) or not path.is_file() or sha256(path) != expected:
            raise DriverSafetyError("Backup integrity check failed")
        files.append(path)
    return files

def restore_preview(directory: Path, devices):
    files = verify_backup(directory)
    candidates = [parse_inf(path) for path in files if path.suffix.lower() == ".inf"]
    return [{"device": d.name, "status": d.status, "candidates": [
        {"inf": Path(r.candidate.inf).name, "score": r.score, "reason": r.reason, "eligible": r.eligible}
        for r in rank(d, candidates) if r.score]} for d in devices]

# Installation stays fail-closed until catalog membership, target OS decorations,
# narrow privilege helper, backup, restore point and rollback are implemented/VM-tested.
# A hash manifest is NEVER accepted as proof of a signed driver package.
