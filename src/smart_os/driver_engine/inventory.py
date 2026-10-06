from __future__ import annotations
from dataclasses import dataclass, asdict
import platform
from ..core.process import powershell, json_rows, UnsupportedPlatform

@dataclass(frozen=True)
class Device:
    instance_id: str
    name: str
    manufacturer: str
    class_name: str
    hardware_ids: tuple[str, ...]
    compatible_ids: tuple[str, ...]
    problem_code: int
    driver_inf: str = ""
    provider: str = ""
    version: str = ""
    date: str = ""
    signed: bool | None = None

    @property
    def status(self):
        if self.problem_code == 28:
            return "missing"
        if self.problem_code:
            return "needs-review"
        if not self.driver_inf:
            return "needs-review"
        return "installed" # Installed is not proof of current/latest version.

    def to_dict(self):
        return asdict(self) | {"status": self.status}

SCRIPT = r"""
$drivers=@{}; Get-CimInstance Win32_PnPSignedDriver | ForEach-Object {$drivers[$_.DeviceID]=$_}
@(Get-CimInstance Win32_PnPEntity -Filter 'Present = True' | ForEach-Object {
  $d=$drivers[$_.PNPDeviceID]; [pscustomobject]@{
  instance_id=$_.PNPDeviceID; name=$_.Name; manufacturer=$_.Manufacturer;
  class_name=$_.PNPClass; hardware_ids=@($_.HardwareID); compatible_ids=@($_.CompatibleID);
  problem_code=[int]$_.ConfigManagerErrorCode; driver_inf=$d.InfName;
  provider=$d.DriverProviderName; version=$d.DriverVersion;
  date=if($d.DriverDate){$d.DriverDate.ToString('yyyy-MM-dd')}else{''}; signed=$d.IsSigned
} }) | ConvertTo-Json -Depth 4 -Compress
"""

def inventory() -> list[Device]:
    if platform.system() != "Windows":
        raise UnsupportedPlatform("No Windows devices are reported on Linux. Run Smart Windows Driver on Windows")
    def strings(values):
        return tuple(v for v in (values or []) if isinstance(v, str) and v)
    result = []
    for row in json_rows(powershell(SCRIPT, timeout=120)):
        result.append(Device(row["instance_id"] or "", row["name"] or "Unknown device",
           row["manufacturer"] or "", row["class_name"] or "", strings(row["hardware_ids"]),
           strings(row["compatible_ids"]), int(row["problem_code"]), row["driver_inf"] or "",
           row["provider"] or "", row["version"] or "", row["date"] or "", row["signed"]))
    return result

def windows_update_drivers() -> list[dict]:
    # Read-only search. Does not install updates or change Windows Update settings.
    return json_rows(powershell(r"""
$s=New-Object -ComObject Microsoft.Update.Session; $q=$s.CreateUpdateSearcher();
$r=$q.Search("IsInstalled=0 and Type='Driver' and IsHidden=0");
@($r.Updates | ForEach-Object { [pscustomobject]@{title=$_.Title;
  manufacturer=$_.DriverManufacturer; model=$_.DriverModel;
  date=[string]$_.DriverVerDate; update_id=$_.Identity.UpdateID} }) | ConvertTo-Json -Compress
""", timeout=300))
