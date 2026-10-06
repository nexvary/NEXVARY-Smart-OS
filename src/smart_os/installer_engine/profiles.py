from __future__ import annotations
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PACKAGES = {
    "normal": {"debian": ["task-desktop"], "ubuntu": [], "kali": ["kali-desktop-xfce"]},
    "developer": {"debian": ["git", "build-essential"], "ubuntu": ["git", "build-essential"], "kali": ["git", "build-essential"]},
    "minimal": {"debian": [], "ubuntu": [], "kali": []},
    "office": {"debian": ["libreoffice"], "ubuntu": ["libreoffice"], "kali": ["libreoffice"]},
    "server": {"debian": ["openssh-server"], "ubuntu": ["openssh-server"], "kali": []},
    "cybersecurity": {"debian": ["nmap"], "ubuntu": ["nmap"], "kali": ["nmap", "wireshark"]},
}

@dataclass(frozen=True)
class InstallationProfile:
    distribution: str
    hostname: str = "smart-os"
    username: str = "user"
    locale: str = "en_US.UTF-8"
    keyboard: str = "us"
    timezone: str = "Africa/Cairo"
    preset: str = "normal"
    schema_version: int = 1

    def validate(self):
        if self.schema_version != 1 or self.distribution not in {"ubuntu", "debian", "kali"}:
            raise ValueError("Unsupported profile schema/distribution")
        if not re.fullmatch(r"[a-z][a-z0-9-]{0,62}", self.hostname) or self.hostname.endswith("-"):
            raise ValueError("Invalid hostname")
        if not re.fullmatch(r"[a-z_][a-z0-9_-]{0,30}", self.username) or self.username == "root":
            raise ValueError("Invalid non-root username")
        if self.locale not in {"en_US.UTF-8", "ar_EG.UTF-8", "tr_TR.UTF-8", "fr_FR.UTF-8", "de_DE.UTF-8", "es_ES.UTF-8", "it_IT.UTF-8"}:
            raise ValueError("Unsupported locale")
        if self.keyboard not in {"us", "ara", "tr", "fr", "de", "es", "it"}:
            raise ValueError("Unsupported keyboard layout")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Unknown timezone") from exc
        if self.preset not in PACKAGES:
            raise ValueError("Unknown package preset")

    def save(self, path: Path):
        self.validate()
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path):
        profile = cls(**json.loads(path.read_text(encoding="utf-8")))
        profile.validate()
        return profile
