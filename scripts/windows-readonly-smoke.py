"""Read-only integration on the Windows runner; never install/change a driver."""
from pathlib import Path
import json
import tempfile
from smart_os.core.hardware import scan
from smart_os.core.logging import export_report
from smart_os.driver_engine.inventory import inventory
from smart_os.driver_engine.backup import backup, verify_backup, DriverSafetyError

hardware=scan()
devices=inventory()
assert hardware.system=='Windows' and hardware.memory_bytes
assert devices, 'No real Windows PnP devices discovered'
result={'system':hardware.system,'architecture':hardware.architecture,
        'devices':len(devices),'missing':sum(d.status=='missing' for d in devices),
        'needs_review':sum(d.status=='needs-review' for d in devices),
        'hardware_ids_present':sum(bool(d.hardware_ids) for d in devices),
        'disk_scan_limitations':hardware.limitations,'driver_installation_tested':False}
with tempfile.TemporaryDirectory() as folder:
    directory=Path(folder)/'oem-driver-backup'
    try:
        exported=backup(directory)
        verified=verify_backup(directory)
        assert any(file.suffix.lower()=='.inf' for file in verified)
        result['driver_backup']={'state':'passed','export':exported,'verified_files':len(verified)}
    except DriverSafetyError as exc:
        if 'No third-party drivers exported' not in str(exc):raise
        result['driver_backup']={'state':'not-tested-no-oem-drivers','reason':str(exc)}
output=Path('artifacts/verification/windows-readonly.json');output.parent.mkdir(parents=True,exist_ok=True)
export_report(output,result)
print(json.dumps(result))
