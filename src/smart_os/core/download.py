from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

OFFICIAL_HOSTS = frozenset({"cdimage.debian.org", "cdimage.ubuntu.com", "releases.ubuntu.com", "cdimage.kali.org", "ftp.acc.umu.se"})
CATALOG = [
    {"distribution": "Ubuntu", "channel": "LTS / interim", "source": "https://releases.ubuntu.com/", "architecture": "Choose official amd64 image"},
    {"distribution": "Debian", "channel": "Stable", "source": "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/", "architecture": "amd64"},
    {"distribution": "Kali", "channel": "Rolling", "source": "https://cdimage.kali.org/", "architecture": "Choose official amd64 installer"},
]

def validate_url(url: str):
    p = urlsplit(url)
    # Debian lists ftp.acc.umu.se as a CD mirror; cdimage redirects to its named servers.
    trusted = p.hostname in OFFICIAL_HOSTS or bool(p.hostname and p.hostname.endswith(".ftp.acc.umu.se"))
    if p.scheme != "https" or not trusted or p.username or p.password or p.port not in {None, 443}:
        raise ValueError("Only allowlisted official HTTPS distribution servers are accepted")

class OfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def download_iso(url: str, expected_sha256: str, destination: Path, max_bytes: int = 16 * 1024**3):
    validate_url(url)
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
        raise ValueError("Authenticated official SHA256 required")
    if destination.exists():
        raise ValueError("Choose a new destination; existing files are never replaced")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".smart-download-", dir=destination.parent)
    try:
        digest, size = hashlib.sha256(), 0
        opener = build_opener(OfficialRedirect())
        with os.fdopen(fd, "wb") as target, opener.open(Request(url, headers={"User-Agent": "NEXVARY-Smart-OS/0.1"}), timeout=30) as response:
            validate_url(response.url)
            for chunk in iter(lambda: response.read(1024 * 1024), b""):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError("Download size limit exceeded")
                digest.update(chunk)
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        if size == 0 or digest.hexdigest() != expected_sha256.lower():
            raise ValueError("Downloaded ISO checksum mismatch")
        # Link refuses an existing destination even if one appears during transfer.
        os.link(temporary, destination)
        return {"bytes": size, "sha256": digest.hexdigest(), "source": url}
    finally:
        Path(temporary).unlink(missing_ok=True)
