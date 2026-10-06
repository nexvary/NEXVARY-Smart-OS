"""Explicit portable profile for offline matching; never uploads anything."""
import json
import platform
from pathlib import Path
from datetime import datetime, timezone

class MachineProfileError(ValueError):pass

def export_profile(path:Path,devices):
    if path.exists():raise MachineProfileError('Choose a new profile filename')
    if not devices:raise MachineProfileError('Scan real devices before exporting a profile')
    data={'schema_version':1,'kind':'smart-driver-machine-profile','created_at':datetime.now(timezone.utc).isoformat(),
          'architecture':platform.machine(),'devices':[{'name':d.name,'class_name':d.class_name,'hardware_ids':list(d.hardware_ids),'compatible_ids':list(d.compatible_ids),'problem_code':d.problem_code} for d in devices],
          'notice':'Contains hardware IDs for offline matching. No serial numbers, instance IDs, passwords or online upload.'}
    with path.open('x',encoding='utf-8') as stream:json.dump(data,stream,indent=2,ensure_ascii=False)
    return {'devices':len(devices),'folder':str(path),'uploaded':False}

def load_profile(path:Path):
    from .inventory import Device
    if path.stat().st_size>4*1024*1024:raise MachineProfileError('Profile exceeds 4 MiB')
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version')!=1 or data.get('kind')!='smart-driver-machine-profile':raise MachineProfileError('Unsupported machine profile')
    if data.get('architecture','').casefold() not in {'amd64','x86_64'}:raise MachineProfileError('Only x64 machine profiles are supported')
    rows=data.get('devices')
    if not isinstance(rows,list) or not rows or len(rows)>4096:raise MachineProfileError('Invalid devices list')
    devices=[]
    for row in rows:
        for key in ['hardware_ids','compatible_ids']:
            ids=row.get(key)
            if not isinstance(ids,list) or len(ids)>128 or any(not isinstance(x,str) or len(x)>1024 for x in ids):raise MachineProfileError('Invalid hardware IDs')
        if not isinstance(row.get('name'),str) or not isinstance(row.get('class_name'),str) or type(row.get('problem_code')) is not int:raise MachineProfileError('Invalid device metadata')
        devices.append(Device('',row['name'], '',row['class_name'],tuple(row['hardware_ids']),tuple(row['compatible_ids']),row['problem_code']))
    return devices
