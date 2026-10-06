"""Unprivileged audit process. Native providers may cache open catalog handles.

A process boundary releases provider caches before returning control to the GUI.
Input is bounded JSON, never code; only read-only native inspection is supported.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from ..core.process import OperationError
from ..core.elevation import helper_command,MAX_REQUEST,MAX_RESPONSE


def inspect(operation,parameters):
    exe,args=helper_command();raw=json.dumps({'schema':1,'operation':operation,'parameters':parameters}).encode()
    if len(raw)>MAX_REQUEST:raise ValueError('Audit request is too large')
    process=subprocess.run([exe,*args,'--audit'],input=raw,capture_output=True,timeout=180,shell=False,
                           creationflags=0x08000000 if sys.platform=='win32' else 0)
    if process.returncode:raise OperationError(f'Driver audit process exited with code {process.returncode}')
    if len(process.stdout)>MAX_RESPONSE:raise OperationError('Driver audit response is too large')
    result=json.loads(process.stdout)
    if result.get('ok') is not True:raise OperationError(result.get('error','Driver audit failed'))
    return result['result']


def dispatch(packet):
    if not isinstance(packet,dict) or set(packet)!={'schema','operation','parameters'} or packet['schema']!=1:raise ValueError('Unsupported audit request')
    op=packet['operation'];params=packet['parameters']
    keys={'verify-package':{'inf','catalog'},'compatible-drivers':{'inf','instance_id'}}
    if not isinstance(op,str) or op not in keys or not isinstance(params,dict) or set(params)!=keys[op]:raise ValueError('Unsupported audit operation')
    if any(not isinstance(v,str) or '\x00' in v or len(v)>32767 for v in params.values()):raise ValueError('Invalid audit parameter')
    if not Path(params['inf']).is_absolute():raise ValueError('Audit INF must be absolute')
    from .native import _verify_package,_compatible_drivers
    if op=='verify-package':return _verify_package(Path(params['inf']),params['catalog']).to_dict()
    return _compatible_drivers(Path(params['inf']),params['instance_id'])


def main():
    try:
        raw=sys.stdin.buffer.read(MAX_REQUEST+1)
        if len(raw)>MAX_REQUEST:raise ValueError('Audit request is too large')
        response={'ok':True,'result':dispatch(json.loads(raw))}
    except Exception as exc:response={'ok':False,'error':str(exc)}
    data=json.dumps(response).encode('ascii') # ensure_ascii is deliberate
    if len(data)>MAX_RESPONSE:data=b'{"ok":false,"error":"Audit result too large"}'
    sys.stdout.buffer.write(data);sys.stdout.buffer.flush();return 0
