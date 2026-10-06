from __future__ import annotations
from dataclasses import asdict, dataclass
import hashlib
import json
from .hardware import Disk

class SafetyError(ValueError):
    pass

@dataclass(frozen=True)
class DiskPlan:
    target: Disk
    purpose: str
    image_sha256: str = ""
    image_size: int = 0

    @property
    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()

    @property
    def confirmation(self):
        return f"ERASE {self.target.path} {self.digest[:12]}"

    def preview(self):
        return {"target": asdict(self.target), "purpose": self.purpose,
                "data_loss": "All data on the selected disk will be erased" if self.purpose == "usb" else "No disk changes; manual partition review required",
                "confirmation": self.confirmation, "digest": self.digest,
                "image_sha256": self.image_sha256, "image_size": self.image_size}

def validate_usb(plan: DiskPlan, current: Disk, confirmation: str):
    if plan.purpose != "usb" or plan.target != current:
        raise SafetyError("Disk identity or partition state changed. Scan and review again")
    if not current.serial:
        raise SafetyError("Stable disk serial unavailable; raw writing is blocked")
    if current.transport.lower() != "usb" or not current.removable:
        raise SafetyError("Only positively identified removable USB disks are allowed")
    if current.mounted or current.readonly:
        raise SafetyError("USB is mounted or read-only; unmount it manually then scan again")
    if current.protected:
        raise SafetyError("Protected/unknown partitions detected; raw writing is blocked")
    if plan.image_size <= 0 or plan.image_size > current.size:
        raise SafetyError("ISO does not fit this USB")
    if len(plan.image_sha256) != 64:
        raise SafetyError("Verified ISO hash required")
    if confirmation != plan.confirmation:
        raise SafetyError("Confirmation must identify this exact disk and plan")

def validate_empty_disk(disk: Disk):
    if not disk.serial or disk.partitions or disk.mounted or disk.readonly or disk.size < 20 * 1024**3:
        raise SafetyError("Only an identified, empty, writable disk of at least 20 GiB is eligible")
