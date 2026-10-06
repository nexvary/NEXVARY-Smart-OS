from __future__ import annotations
import json
import platform
from pathlib import Path
from dataclasses import dataclass, field, asdict
from .process import run, powershell, json_rows

@dataclass(frozen=True)
class Partition:
    path: str
    size: int
    filesystem: str = ""
    kind: str = "unknown"
    mounted: bool = False

@dataclass(frozen=True)
class Disk:
    path: str
    size: int
    model: str = ""
    serial: str = ""
    transport: str = ""
    removable: bool = False
    readonly: bool = False
    partitions: tuple[Partition, ...] = ()

    @property
    def protected(self):
        return any(p.kind in {"windows", "efi", "recovery", "oem", "unknown", "data"} for p in self.partitions)

    @property
    def mounted(self):
        return any(p.mounted for p in self.partitions)

@dataclass
class Inventory:
    system: str
    architecture: str
    cpu: str
    memory_bytes: int | None
    boot_mode: str
    secure_boot: str
    disks: list[Disk] = field(default_factory=list)
    devices: list[dict] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

def classify_partition(fs: str, parttype: str, label: str) -> str:
    fs, parttype, label = fs.lower(), parttype.lower(), label.lower()
    if parttype == "c12a7328-f81f-11d2-ba4b-00a0c93ec93b":
        return "efi"
    if parttype in {"de94bba4-06d1-4d40-a16a-bfd50179d6ac", "27"} or "recovery" in label:
        return "recovery"
    if "oem" in label or parttype == "e3c9e316-0b5c-4db8-817d-f92df00215ae":
        return "oem"
    if fs in {"ntfs", "bitlocker"}:
        return "windows" # Conservative: NTFS might be data; protect either way.
    if fs in {"ext2", "ext3", "ext4", "btrfs", "xfs", "swap"}:
        return "linux"
    return "data" if fs else "unknown"

def linux_disks(rows: list[dict]) -> list[Disk]:
    def partitions(node):
        result = []
        for child in node.get("children", []):
            mounts = child.get("mountpoints") or [child.get("mountpoint")]
            if child.get("type") == "part":
                fs = child.get("fstype") or ""
                result.append(Partition(child["path"], int(child.get("size") or 0), fs,
                    classify_partition(fs, child.get("parttype") or "", child.get("label") or ""),
                    any(mounts) or any_grandchild_mounted(child)))
            else:
                result.extend(partitions(child))
        return result
    def any_grandchild_mounted(node):
        return any(any(c.get("mountpoints") or [c.get("mountpoint")]) or any_grandchild_mounted(c)
                   for c in node.get("children", []))
    return [Disk(row["path"], int(row.get("size") or 0), (row.get("model") or "").strip(),
                 row.get("serial") or "", row.get("tran") or "", bool(row.get("rm")),
                 bool(row.get("ro")), tuple(partitions(row)) + (
                     (Partition(row["path"], int(row.get("size") or 0), row.get("fstype") or "",
                                classify_partition(row.get("fstype") or "", "", row.get("label") or ""),
                                any(row.get("mountpoints") or [row.get("mountpoint")]) or any_grandchild_mounted(row)),)
                     if row.get("fstype") or any(row.get("mountpoints") or [row.get("mountpoint")]) else ()))
            for row in rows if row.get("type") == "disk"]

def scan_disks() -> list[Disk]:
    if platform.system() == "Linux":
        data = json.loads(run(["lsblk", "--json", "--bytes", "--paths", "--output",
              "PATH,SIZE,MODEL,SERIAL,TRAN,RM,RO,TYPE,FSTYPE,PARTTYPE,LABEL,MOUNTPOINTS"]))
        return linux_disks(data["blockdevices"])
    if platform.system() == "Windows":
        script = """@(Get-Disk | ForEach-Object {
        $d=$_; $p=@(Get-Partition -DiskNumber $d.Number | ForEach-Object {
          $v=$_ | Get-Volume -ErrorAction SilentlyContinue
          [pscustomobject]@{path=[string]$_.PartitionNumber; size=$_.Size;
           fs=[string]$v.FileSystem; type=[string]$_.GptType; label=[string]$v.FileSystemLabel;
           mounted=([bool]$_.DriveLetter -or $d.IsBoot -or $d.IsSystem)} })
        [pscustomobject]@{path=('\\\\.\\PhysicalDrive'+$d.Number); size=$d.Size;
        model=$d.FriendlyName; serial=$d.SerialNumber; transport=[string]$d.BusType;
        readonly=$d.IsReadOnly; partitions=$p} }) | ConvertTo-Json -Depth 5 -Compress"""
        result = []
        for d in json_rows(powershell(script)):
            parts = tuple(Partition(p["path"], int(p["size"]), p["fs"],
                    classify_partition(p["fs"], p["type"].strip("{}"), p["label"]), p["mounted"])
                    for p in d.get("partitions", []))
            result.append(Disk(d["path"], int(d["size"]), d["model"], d["serial"], d["transport"],
                               d["transport"] == "USB", d["readonly"], parts))
        return result
    raise RuntimeError("Hardware scanning supports Linux or Windows")

def scan() -> Inventory:
    system = platform.system()
    report = Inventory(system, platform.machine(), platform.processor() or platform.machine(),
                       None, "unknown", "unknown")
    if system == "Linux":
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            report.cpu = next(line.split(":", 1)[1].strip() for line in cpuinfo.splitlines() if line.startswith("model name"))
            report.memory_bytes = int(next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemTotal:"))) * 1024
        except (OSError, StopIteration):
            report.limitations.append("CPU/RAM unavailable")
        report.boot_mode = "UEFI" if Path("/sys/firmware/efi").is_dir() else "Legacy or virtualized; EFI not exposed"
        variables = list(Path("/sys/firmware/efi/efivars").glob("SecureBoot-*"))
        if variables:
            try:
                payload = variables[0].read_bytes()
                report.secure_boot = "enabled" if len(payload) > 4 and payload[4] == 1 else "disabled"
            except OSError:
                pass
        for base in ["/sys/bus/pci/devices", "/sys/bus/usb/devices"]:
            for dev in Path(base).glob("*"):
                item = {"bus": "PCI" if "/pci/" in base else "USB"}
                for attr in ["vendor", "device", "class", "idVendor", "idProduct", "product"]:
                    try:
                        item[attr] = (dev / attr).read_text().strip()
                    except OSError:
                        pass
                if len(item) > 1:
                    report.devices.append(item)
        report.limitations.extend(["Firmware compatibility is not inferred from device names", "Container inventory may describe the host; review disks on the target machine"])
    elif system == "Windows":
        facts = json.loads(powershell("""$c=Get-CimInstance Win32_ComputerSystem; $p=Get-CimInstance Win32_Processor | Select-Object -First 1;
        $s='unknown'; try {$s=[string](Confirm-SecureBootUEFI)} catch {}
        [pscustomobject]@{cpu=$p.Name; ram=$c.TotalPhysicalMemory; secureboot=$s} | ConvertTo-Json -Compress"""))
        report.cpu, report.memory_bytes, report.secure_boot = facts["cpu"], int(facts["ram"]), facts["secureboot"]
        report.limitations.append("Boot mode, BitLocker, Fast Startup and firmware coverage need separate checks")
    else:
        report.limitations.append("Unsupported operating system")
    try:
        report.disks = scan_disks()
    except Exception as exc:
        report.limitations.append(f"Disk scan unavailable: {type(exc).__name__}")
    return report
