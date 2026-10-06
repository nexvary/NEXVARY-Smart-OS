from __future__ import annotations
import os
import stat
from pathlib import Path
from ..core.hardware import scan_disks
from ..core.safety import DiskPlan, SafetyError, validate_usb
from .iso import sha256

def write_usb(plan: DiskPlan, image: Path, confirmation: str, scanner=scan_disks):
    """Linux only. Strict preflight, device recheck, raw write, readback hash."""
    if os.name == "nt":
        raise SafetyError("Windows raw USB writing has not been validated; blocked in this alpha")
    if os.geteuid() != 0:
        raise SafetyError("A privileged, narrowly scoped USB helper is required")
    current = next((disk for disk in scanner() if disk.path == plan.target.path), None)
    if current is None:
        raise SafetyError("USB no longer present")
    validate_usb(plan, current, confirmation)
    if sha256(image) != plan.image_sha256 or image.stat().st_size != plan.image_size:
        raise SafetyError("ISO changed after preview")
    target = Path(current.path)
    if not stat.S_ISBLK(target.stat().st_mode):
        raise SafetyError("Target is not a block device")
    # O_EXCL refuses mounted/busy block devices. O_NOFOLLOW refuses symlinks.
    fd = os.open(str(target), os.O_WRONLY | os.O_EXCL | os.O_NOFOLLOW)
    try:
        new = next((d for d in scanner() if d.path == current.path), None)
        if new != current:
            raise SafetyError("USB changed before opening")
        with image.open("rb") as source:
            for chunk in iter(lambda: source.read(4 * 1024 * 1024), b""):
                view = memoryview(chunk)
                while view:
                    count = os.write(fd, view)
                    if count <= 0:
                        raise OSError("USB write failed")
                    view = view[count:]
        os.fsync(fd)
    finally:
        os.close(fd)
    import hashlib
    digest, remaining = hashlib.sha256(), plan.image_size
    with target.open("rb") as stream:
        while remaining:
            chunk = stream.read(min(4 * 1024 * 1024, remaining))
            if not chunk:
                raise OSError("USB readback ended early")
            digest.update(chunk)
            remaining -= len(chunk)
    if digest.hexdigest() != plan.image_sha256:
        raise OSError("USB readback checksum mismatch; media must not be used")
    return {"state": "verified", "bytes_written": plan.image_size}
