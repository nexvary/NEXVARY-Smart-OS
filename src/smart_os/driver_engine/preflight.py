"""A reviewable install plan; active device mutation is still VM-gated."""
from __future__ import annotations
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from .inventory import Device
from .matching import parse_inf, rank
from .native import verify_package, compatible_drivers
from ..core.integrity import sha256


def review_driver(inf:Path,device:Device)->dict:
    inf=Path(inf).resolve(strict=True)
    candidate=parse_inf(inf)
    basic=rank(device,[candidate])[0]
    result={'device':device.name,'inf':str(inf),'match':basic.reason,'trust_verified':False,
            'native_compatible':False,'preflight_passed':False,'installation':'blocked-in-alpha',
            'recovery':{'backup_required':bool(device.driver_inf),'restore_point':'not-created','rollback':'not-validated'}}
    if not basic.score:
        result['reason']=basic.reason;return result
    trust=verify_package(inf,candidate.catalog);result['trust']=trust.to_dict();result['trust_verified']=trust.verified
    if not trust.verified:result['reason']=trust.reason;return result
    native=compatible_drivers(inf,device.instance_id);result['native_candidates']=native;result['native_compatible']=bool(native)
    exact=bool({x.upper() for x in device.hardware_ids}&set(candidate.hardware_ids))
    if not exact:result['reason']='Compatible ID only; explicit OEM review is required';return result
    if not native:result['reason']='Windows found no compatible driver for the current OS and device';return result
    if device.class_name.casefold() in {'firmware','system','scsiadapter','hdc','securitydevices'}:
        result['reason']='Sensitive driver class needs a separately validated recovery workflow';return result
    files={p.relative_to(inf.parent).as_posix():sha256(p) for p in sorted(inf.parent.rglob('*')) if p.is_file()}
    payload={'inf':inf.name,'instance_id':device.instance_id,'current_inf':device.driver_inf,'current_version':device.version,'files':files}
    result['plan_digest']=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result['preflight_passed']=True
    result['reason']='Signature, payload membership, exact Hardware ID and native Windows compatibility passed; installation/rollback VM gate remains pending'
    # A plan digest is not permission to execute. No command list is exposed.
    return result
