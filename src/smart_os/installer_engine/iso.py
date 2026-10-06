from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib
import io
from pathlib import Path
import re
import pycdlib

class ISOError(ValueError):
    pass

from ..core.integrity import sha256

@dataclass(frozen=True)
class ISOReport:
    path: str
    size: int
    sha256: str
    checksum_status: str
    distribution: str
    release_label: str
    installer: str
    architecture: str
    uefi: bool
    legacy: bool
    files: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_dict(self):
        return asdict(self)

def analyze(path: Path, expected_sha256: str | None = None) -> ISOReport:
    path = path.resolve(strict=True)
    if not path.is_file():
        raise ISOError("Select a regular ISO file")
    digest = sha256(path)
    if expected_sha256 is not None:
        expected_sha256 = expected_sha256.strip().lower()
        if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
            raise ISOError("SHA256 must contain exactly 64 hexadecimal characters")
        if expected_sha256 != digest:
            raise ISOError("Checksum mismatch. Do not use this image")
    iso = pycdlib.PyCdlib()
    try:
        iso.open(str(path))
        listing = []
        walk_key = "rr_path" if iso.has_rock_ridge() else "joliet_path" if iso.has_joliet() else "iso_path"
        for directory, _, files in iso.walk(**{walk_key: "/"}):
            for filename in files:
                listing.append((directory.rstrip("/") + "/" + filename).split(";")[0].lower())
                if len(listing) > 200000:
                    raise ISOError("ISO file count limit exceeded")
        label = ""
        for candidate in ["/.disk/info", "/.disk/release_notes_url"]:
            stream = io.BytesIO()
            for key in ["rr_path", "joliet_path", "iso_path"]:
                try:
                    record = iso.get_record(**{key: candidate})
                    if record.data_length > 8192:
                        continue
                    iso.get_file_from_iso_fp(stream, **{key: candidate})
                    label += stream.getvalue().decode("utf-8", "replace")[:8192]
                    break
                except (pycdlib.pycdlibexception.PyCdlibException, AttributeError, IndexError, KeyError):
                    continue
        # Metadata, not the user-controlled filename, determines distribution.
        label_lower = label.lower()
        distro = next((d for d in ["kali", "ubuntu", "debian"] if d in label_lower), "unknown")
        names = set(listing)
        installer = "unknown"
        if "/casper/install-sources.yaml" in names and distro == "ubuntu":
            installer = "subiquity-candidate" # Desktop variants require version-specific validation.
        elif any("install.amd/" in x or "install.a64/" in x for x in names):
            installer = "debian-installer" if distro in {"debian", "kali"} else "unknown"
        elif any("/live/" in x for x in names):
            installer = "live-image-unverified"
        arch = next((a for a in ["amd64", "arm64", "i386"] if a in label_lower), "unknown")
        catalog = getattr(iso, "eltorito_boot_catalog", None)
        entries = []
        if catalog:
            entries.append(catalog.initial_entry)
            for section in catalog.sections:
                entries.extend(section.section_entries)
        uefi = any("/efi/boot/" in x for x in listing)
        legacy = bool(catalog and catalog.validation_entry.platform_id == 0 and catalog.initial_entry.boot_indicator == 0x88)
        warnings = []
        if not expected_sha256:
            warnings.append("Hash computed only; verify against an authenticated official checksum")
        if distro == "unknown" or installer in {"unknown", "live-image-unverified"}:
            warnings.append("Installer cannot be established safely; unattended configuration blocked")
        if uefi:
            warnings.append("EFI boot files found; Secure Boot signature compatibility has not been verified")
        return ISOReport(str(path), path.stat().st_size, digest,
            "verified-against-supplied-hash" if expected_sha256 else "unverified", distro,
            label.strip(), installer, arch, uefi, legacy, tuple(listing), tuple(warnings))
    except pycdlib.pycdlibexception.PyCdlibException as exc:
        raise ISOError("Invalid or unsupported ISO structure") from exc
    finally:
        try:
            iso.close()
        except pycdlib.pycdlibexception.PyCdlibException:
            pass
