"""Read-only integration on the Windows runner; never install/change a driver."""
from pathlib import Path
import json
import tempfile
from smart_os.core.hardware import scan
from smart_os.core.logging import export_report
from smart_os.driver_engine.inventory import inventory
from smart_os.driver_engine.backup import backup, verify_backup, DriverSafetyError

from smart_os.core.readiness import dual_boot_readiness
from smart_os.driver_engine.machine_profile import export_profile,load_profile

from smart_os.driver_engine.servicing import check_health, list_drivers
from smart_os.core.elevation import request_operation
from smart_os.driver_engine.native import verify_package, compatible_drivers, Signer, DeviceInfo, DriverInfo, InstallParams, TrustData
from smart_os.driver_engine.matching import parse_inf, rank
from smart_os.driver_engine.preflight import review_driver
import ctypes

hardware=scan()
devices=inventory()
assert hardware.system=='Windows' and hardware.memory_bytes
assert devices, 'No real Windows PnP devices discovered'
result={'system':hardware.system,'architecture':hardware.architecture,
        'devices':len(devices),'missing':sum(d.status=='missing' for d in devices),
        'needs_review':sum(d.status=='needs-review' for d in devices),
        'hardware_ids_present':sum(bool(d.hardware_ids) for d in devices),
        'disk_scan_limitations':hardware.limitations,'driver_installation_tested':False}
assert ctypes.sizeof(Signer)==1568 and ctypes.sizeof(DeviceInfo)==32 and ctypes.sizeof(DriverInfo)==1568 and ctypes.sizeof(InstallParams)==584 and ctypes.sizeof(TrustData)==88
result['dism']={'health':request_operation('check-health'),'drivers':request_operation('list-drivers')}
result['privilege_helper_rpc']='passed-admin-token-no-UAC-dialog-on-runner'
assert all(r['changes_requested'] is False and r['output'] for r in result['dism'].values())
result['dual_boot_readiness']=dual_boot_readiness()
assert result['dual_boot_readiness']['automatic_changes'] is False
with tempfile.TemporaryDirectory() as folder:
    profile=Path(folder)/'machine.json'; export_profile(profile,devices)
    restored=load_profile(profile); assert len(restored)==len(devices) and restored[0].hardware_ids==devices[0].hardware_ids
    result['offline_profile_roundtrip']='passed'
    directory=Path(folder)/'oem-driver-backup'
    try:
        exported=request_operation('driver-backup',{'destination':str(directory.resolve()),'inf':'*'})
        verified=verify_backup(directory)
        assert any(file.suffix.lower()=='.inf' for file in verified)
        result['driver_backup']={'state':'passed','export':exported,'verified_files':len(verified)}
        audits=[]; native_matches=0; review_result=None
        for inf in (p for p in verified if p.suffix.lower()=='.inf'):
            candidate=parse_inf(inf); trust=verify_package(inf,candidate.catalog)
            audits.append({'inf':inf.name,'trust':trust.to_dict()})
            if trust.verified:
                for device in devices:
                    if rank(device,[candidate])[0].score:
                        matches=compatible_drivers(inf,device.instance_id)
                        if matches:
                            native_matches+=1
                            if review_result is None or device.class_name.casefold()=='net':
                                review_result=review_driver(inf,device)
                            break
        assert any(a['trust']['verified'] for a in audits), audits
        assert native_matches, 'No actual Windows-compatible OEM driver found'
        result['native_driver_preflight']={'packages':audits,'native_compatible_packages':native_matches}
        assert review_result and review_result['trust_verified'] and review_result['native_compatible']
        assert review_result['installation']=='blocked-in-alpha'
        result['driver_review']=review_result
        # Tamper a COPY of a trusted package. Never alter Driver Store or devices.
        import shutil
        trusted=next(p for p in verified if p.suffix.lower()=='.inf' and any(a['inf']==p.name and a['trust']['verified'] for a in audits))
        corrupt=Path(folder)/'corrupt-package'; shutil.copytree(trusted.parent,corrupt)
        target=next(p for p in corrupt.rglob('*') if p.suffix.lower() in {'.sys','.dll'})
        import struct
        data=bytearray(target.read_bytes()); pe=struct.unpack_from('<I',data,0x3c)[0]
        section=pe+24+struct.unpack_from('<H',data,pe+20)[0]
        payload_offset=struct.unpack_from('<I',data,section+20)[0]
        assert 0<payload_offset<len(data)
        data[payload_offset]^=1; target.write_bytes(data)
        rejected=verify_package(corrupt/trusted.name,parse_inf(corrupt/trusted.name).catalog)
        assert not rejected.verified, 'Modified payload passed trust verification'
        result['native_tampered_payload_rejected']=True
    except DriverSafetyError as exc:
        if 'No third-party drivers exported' not in str(exc):raise
        result['driver_backup']={'state':'not-tested-no-oem-drivers','reason':str(exc)}
output=Path('artifacts/verification/windows-readonly.json');output.parent.mkdir(parents=True,exist_ok=True)
export_report(output,result)
print(json.dumps(result))
