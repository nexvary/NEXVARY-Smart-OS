"""One-operation UAC helper. Local message pipe; no arbitrary commands or scripts.

Only DISM inspection and creation of new OEM driver backups are enabled.
Installation/removal, reboot and shell execution are not protocol operations.
"""
from __future__ import annotations
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from .windows import dll, function, D, P, W
from .process import OperationError, UnsupportedPlatform

MAX_REQUEST=16384; MAX_RESPONSE=2*1024*1024
PREFIX='\\\\.\\pipe\\NEXVARY-SmartOS-'

class ElevationCancelled(OperationError):pass
class SecurityAttributes(C.Structure):
    _fields_=[('size',D),('descriptor',P),('inherit',C.c_int)]
class ShellExecuteInfo(C.Structure):
    _fields_=[('size',D),('mask',D),('window',P),('verb',W),('file',W),('parameters',W),('directory',W),('show',C.c_int),('instance',P),('idlist',P),('class_name',W),('class_key',P),('hotkey',D),('icon',P),('process',P)]


def validate_request(request):
    if not isinstance(request,dict) or set(request)!={'schema','nonce','operation','parameters'} or request['schema']!=1:
        raise ValueError('Unsupported privilege request')
    if not isinstance(request['nonce'],str) or not re.fullmatch('[0-9a-f]{32}',request['nonce']):raise ValueError('Invalid request nonce')
    op=request['operation'];params=request['parameters']
    allowed={'check-health':set(),'list-drivers':set(),'image-info':{'path'},'driver-backup':{'destination','inf'}}
    if not isinstance(op,str) or op not in allowed or not isinstance(params,dict) or set(params)!=allowed[op]:
        raise ValueError('Privilege operation or parameters not allowed')
    for key,value in params.items():
        if not isinstance(value,str) or not value or '\x00' in value or len(value)>32767:raise ValueError('Invalid privilege parameter')
        if key!='inf' and not Path(value).is_absolute():raise ValueError('Privilege paths must be absolute')
    if op=='driver-backup' and params['inf']!='*' and not re.fullmatch('oem[0-9]+\\.inf',params['inf'],re.I):raise ValueError('Invalid OEM INF name')
    if len(json.dumps(request).encode())>MAX_REQUEST:raise ValueError('Privilege request too large')
    return request


def dispatch(request):
    validate_request(request)
    # Fixed imports and fixed operations; never supplied module/executable/script.
    from ..driver_engine.servicing import check_health, list_drivers, image_info
    from ..driver_engine.backup import backup
    params=request['parameters']
    if request['operation']=='check-health':return check_health()
    if request['operation']=='list-drivers':return list_drivers()
    if request['operation']=='image-info':return image_info(Path(params['path']))
    return backup(Path(params['destination']),params['inf'])


def _current_sid(kernel,advapi):
    token=P();open_token=function(advapi,'OpenProcessToken',[P,D,C.POINTER(P)],C.c_int)
    info=function(advapi,'GetTokenInformation',[P,D,P,D,C.POINTER(D)],C.c_int)
    convert=function(advapi,'ConvertSidToStringSidW',[P,C.POINTER(W)],C.c_int)
    close=function(kernel,'CloseHandle',[P],C.c_int);free=function(kernel,'LocalFree',[P],P)
    if not open_token(P(-1),8,C.byref(token)):raise OSError('Cannot identify pipe owner')
    try:
        size=D();info(token,1,None,0,C.byref(size));buf=C.create_string_buffer(size.value)
        if not info(token,1,buf,size,C.byref(size)):raise OSError('Cannot inspect pipe owner')
        sid=C.cast(buf,C.POINTER(P))[0];text=W()
        if not convert(sid,C.byref(text)):raise OSError('Cannot format pipe owner')
        try:return text.value
        finally:free(C.cast(text,P))
    finally:close(token)


def _write(kernel,handle,data):
    written=D();fn=function(kernel,'WriteFile',[P,P,D,C.POINTER(D),P],C.c_int)
    buf=C.create_string_buffer(data)
    if not fn(handle,buf,len(data),C.byref(written),None) or written.value!=len(data):raise OperationError('Privilege pipe write failed')


def _read(kernel,handle,limit,timeout):
    fn=function(kernel,'ReadFile',[P,P,D,C.POINTER(D),P],C.c_int)
    deadline=time.monotonic()+timeout;data=bytearray()
    while time.monotonic()<deadline:
        buf=C.create_string_buffer(65536);size=D();ok=fn(handle,buf,len(buf),C.byref(size),None);error=C.get_last_error()
        if size.value:data.extend(buf.raw[:size.value])
        if len(data)>limit:raise OperationError('Privilege response exceeds size limit')
        if ok:return bytes(data)
        if error==234:continue # more message data
        if error in {232,536}:time.sleep(.05);continue
        raise OperationError('Privilege helper disconnected')
    raise OperationError('Privilege helper timed out')


def helper_command():
    if getattr(sys,'frozen',False):
        exe=Path(sys.executable).resolve().parent/'_privilege'/'SmartOSPrivilegeHelper.exe'
        if not exe.is_file():raise OperationError('Installed privilege helper is missing')
        return str(exe),[]
    script=Path(__file__).resolve().parents[3]/'apps/privilege-helper/main.py'
    if not script.is_file():raise OperationError('Development privilege helper is missing')
    return str(Path(sys.executable).resolve()),[str(script)]


def request_operation(operation,parameters=None):
    request=validate_request({'schema':1,'nonce':uuid.uuid4().hex,'operation':operation,'parameters':parameters or {}})
    kernel=dll('kernel32.dll');advapi=dll('advapi32.dll');shell=dll('shell32.dll')
    sid=_current_sid(kernel,advapi);descriptor=P()
    convert=function(advapi,'ConvertStringSecurityDescriptorToSecurityDescriptorW',[W,D,C.POINTER(P),P],C.c_int)
    if not convert(f'D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GA;;;{sid})',1,C.byref(descriptor),None):raise OSError('Pipe security unavailable')
    pipe=P();process=P();free=function(kernel,'LocalFree',[P],P);close=function(kernel,'CloseHandle',[P],C.c_int)
    try:
        attrs=SecurityAttributes(C.sizeof(SecurityAttributes),descriptor,False);name=PREFIX+request['nonce']
        create=function(kernel,'CreateNamedPipeW',[W,D,D,D,D,D,D,C.POINTER(SecurityAttributes)],P)
        handle=create(name,3|0x80000,4|2|1|8,1,MAX_RESPONSE,MAX_REQUEST,0,C.byref(attrs))
        if handle in (None,C.c_void_p(-1).value):raise OSError('Cannot create protected local pipe')
        pipe=P(handle);exe,arguments=helper_command();arguments+=['--pipe',name,'--server-pid',str(os.getpid())]
        info=ShellExecuteInfo();info.size=C.sizeof(info);info.mask=0x40|0x100|0x400;info.verb='runas';info.file=exe;info.parameters=subprocess.list2cmdline(arguments);info.show=0
        ole=dll('ole32.dll'); initialize=function(ole,'CoInitializeEx',[P,D],C.c_int32); uninitialize=function(ole,'CoUninitialize',[],None)
        com=initialize(None,2)
        execute=function(shell,'ShellExecuteExW',[C.POINTER(ShellExecuteInfo)],C.c_int)
        try:launched=execute(C.byref(info));launch_error=C.get_last_error()
        finally:
            if com in (0,1):uninitialize()
        if not launched:
            if launch_error==1223:raise ElevationCancelled('Administrator permission was cancelled; operation did not start')
            raise OperationError('Unable to start the privilege helper')
        process=P(info.process)
        if not process.value:raise OperationError('Privilege process handle unavailable')
        pid=function(kernel,'GetProcessId',[P],D)(process)
        connected=function(kernel,'ConnectNamedPipe',[P,P],C.c_int);client_pid=function(kernel,'GetNamedPipeClientProcessId',[P,C.POINTER(D)],C.c_int)
        deadline=time.monotonic()+60
        while time.monotonic()<deadline:
            connected(pipe,None)
            actual=D()
            if client_pid(pipe,C.byref(actual)):
                if actual.value!=pid:raise OperationError('Unexpected privilege pipe client')
                break
            time.sleep(.05)
        else:raise OperationError('Privilege helper did not connect')
        raw=json.dumps(request,separators=(',',':')).encode();_write(kernel,pipe,raw)
        response=json.loads(_read(kernel,pipe,MAX_RESPONSE,330))
        if not isinstance(response,dict) or response.get('nonce')!=request['nonce'] or response.get('request_hash')!=hashlib.sha256(raw).hexdigest():raise OperationError('Privilege response does not match request')
        if response.get('ok') is not True:raise OperationError(response.get('error','Privilege operation failed'))
        return response['result']
    finally:
        if process.value:close(process)
        if pipe.value:close(pipe)
        free(descriptor)


def serve(pipe_name,server_pid):
    if not pipe_name.startswith(PREFIX) or not re.fullmatch('[0-9a-f]{32}',pipe_name[len(PREFIX):]) or server_pid<=0:raise ValueError('Invalid local pipe identity')
    kernel=dll('kernel32.dll');shell=dll('shell32.dll')
    admin=function(shell,'IsUserAnAdmin',[],C.c_int)
    if not admin():raise OperationError('Privilege helper is not elevated')
    wait=function(kernel,'WaitNamedPipeW',[W,D],C.c_int)
    if not wait(pipe_name,30000):raise OperationError('Privilege server is unavailable')
    create=function(kernel,'CreateFileW',[W,D,D,P,D,D,P],P);close=function(kernel,'CloseHandle',[P],C.c_int)
    handle=create(pipe_name,0xc0000000,0,None,3,0,None)
    if handle in (None,C.c_void_p(-1).value):raise OperationError('Cannot open privilege pipe')
    try:
        actual=D();get_pid=function(kernel,'GetNamedPipeServerProcessId',[P,C.POINTER(D)],C.c_int)
        if not get_pid(handle,C.byref(actual)) or actual.value!=server_pid:raise OperationError('Unexpected privilege server')
        mode=D(3);set_mode=function(kernel,'SetNamedPipeHandleState',[P,C.POINTER(D),P,P],C.c_int)
        if not set_mode(handle,C.byref(mode),None,None):raise OperationError('Pipe message mode unavailable')
        raw=_read(kernel,handle,MAX_REQUEST,30);request=json.loads(raw);validate_request(request)
        if request['nonce']!=pipe_name[len(PREFIX):]:raise OperationError('Request does not match pipe identity')
        response={'nonce':request['nonce'],'request_hash':hashlib.sha256(raw).hexdigest()}
        try:response.update(ok=True,result=dispatch(request))
        except Exception as exc:response.update(ok=False,error=str(exc))
        data=json.dumps(response).encode()
        if len(data)>MAX_RESPONSE:raise OperationError('Privilege result exceeds size limit')
        _write(kernel,handle,data)
        # The peer reads before its handles close; Windows buffers the message.
    finally:close(handle)
