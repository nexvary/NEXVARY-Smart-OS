from __future__ import annotations
from dataclasses import dataclass, asdict
import re

@dataclass(frozen=True)
class Finding:
    code: str
    explanation: str
    suggestion: str
    automatic_repair: bool = False

PATTERNS = [
    (r"grub.*(fail|error)|failed.*grub", "grub-failure", "Bootloader installation failed", "Check EFI mount and boot mode in a rescue environment"),
    (r"temporary failure resolving|name.*resolution|dns.*fail", "dns-failure", "DNS resolution failed", "Check DNS and gateway; retry connectivity before package operations"),
    (r"no space left|insufficient.*space", "disk-full", "Insufficient free space", "Review partition plan; do not delete partitions automatically"),
    (r"hash.*mismatch|checksum.*mismatch", "checksum-mismatch", "Integrity verification failed", "Discard the failed download and obtain an authenticated official checksum"),
    (r"timed out|timeout|failed to fetch", "repository-timeout", "Repository or network connection failed", "Check connectivity and select an official mirror"),
    (r"unmet dependencies|broken packages", "package-dependencies", "Package dependencies could not be resolved", "Review repository release consistency before repairing APT"),
    (r"firmware.*(missing|failed)|failed.*firmware", "missing-firmware", "Firmware could not be loaded", "Find the official firmware package for this chipset"),
    (r"secure boot|efi.*(fail|error)", "boot-review", "Boot configuration needs review", "Check UEFI and Secure Boot compatibility"),
]

def analyze_log(content: str) -> list[Finding]:
    if len(content) > 8 * 1024 * 1024:
        raise ValueError("Log too large; select a log below 8 MiB")
    return [Finding(code, explanation, suggestion) for pattern, code, explanation, suggestion in PATTERNS if re.search(pattern, content, re.I)]
