from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from .inventory import Device

@dataclass(frozen=True)
class Candidate:
    inf: str
    hardware_ids: tuple[str, ...]
    architecture: str
    catalog: str
    provider: str
    version: str
    signature_verified: bool = False
    oem_compatible: bool = False

@dataclass(frozen=True)
class Ranking:
    candidate: Candidate
    score: int
    reason: str
    eligible: bool

def parse_inf(path: Path) -> Candidate:
    raw = path.read_bytes()
    text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig", "replace")
    section, sections = "", {}
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].lower(); sections.setdefault(section, [])
        elif line:
            sections.setdefault(section, []).append(line)
    versions = {}
    for line in sections.get("version", []):
        if "=" in line:
            k, v = line.split("=", 1); versions[k.strip().lower()] = v.strip().strip('"')
    ids = []
    for name, lines in sections.items():
        # Conservative support: only model sections explicitly decorated NTamd64.
        if ".ntamd64" not in name:
            continue
        for line in lines:
            if "=" not in line:
                continue
            fields = line.split("=", 1)[1].split(",")[1:]
            ids.extend(x.strip().strip('"').upper() for x in fields if re.match(r"(?i)\s*(PCI|USB|ACPI|HDAUDIO|BTH|HID|ROOT|VMBUS|SWC|SWD|DISPLAY|SCSI)\\", x))
    catalog = versions.get("catalogfile.ntamd64", versions.get("catalogfile", ""))
    if catalog and (Path(catalog).name != catalog or any(c in catalog for c in "\\/:")):
        raise ValueError("Unsafe catalog filename")
    return Candidate(str(path.resolve()), tuple(dict.fromkeys(ids)), "amd64" if ids else "unknown",
                     catalog, versions.get("provider", ""), versions.get("driverver", ""))

def rank(device: Device, candidates: list[Candidate], architecture="amd64") -> list[Ranking]:
    hardware = {x.upper() for x in device.hardware_ids}
    compatible = {x.upper() for x in device.compatible_ids}
    result = []
    for c in candidates:
        ids = {x.upper() for x in c.hardware_ids}
        if c.architecture != architecture:
            result.append(Ranking(c, 0, "Architecture not supported", False)); continue
        exact, generic = bool(ids & hardware), bool(ids & compatible)
        if not exact and not generic:
            result.append(Ranking(c, 0, "No matching Hardware ID", False)); continue
        score = 10000 if exact else 1000
        if c.signature_verified: score += 100
        if c.oem_compatible: score += 50
        reason = "Exact hardware ID" if exact else "Compatible ID; manual review required"
        if not c.signature_verified: reason += "; signature not verified"
        result.append(Ranking(c, score, reason, exact and c.signature_verified))
    return sorted(result, key=lambda r: r.score, reverse=True)
