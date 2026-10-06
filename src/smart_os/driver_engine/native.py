"""Read-only Windows trust and compatible-driver inspection. No installation APIs."""
from __future__ import annotations
import ctypes as C
import os
import platform
from pathlib import Path
from dataclasses import dataclass, asdict
from ..core.process import UnsupportedPlatform

D=C.c_uint32; P=C.c_void_p; W=C.c_wchar_p; U=C.c_size_t
class GUID(C.Structure):
    _fields_=[('a',D),('b',C.c_uint16),('c',C.c_uint16),('d',C.c_ubyte*8)]
    @classmethod
    def from_text(cls,text):
        import uuid
        return cls.from_buffer_copy(uuid.UUID(text).bytes_le)
class Signer(C.Structure):
    _fields_=[('size',D),('catalog',C.c_wchar*260),('signer',C.c_wchar*260),('version',C.c_wchar*260),('score',D)]
class CatalogInfo(C.Structure):
    _fields_=[('size',D),('version',D),('catalog',W),('tag',W),('member',W),('handle',P),('hash',P),('hash_size',D),('context',P),('admin',P)]
class TrustData(C.Structure):
    _fields_=[('size',D),('policy',P),('sip',P),('ui',D),('revocation',D),('choice',D),('subject',P),('state_action',D),('state',P),('url',W),('flags',D),('ui_context',D),('settings',P)]
class DeviceInfo(C.Structure):
    _fields_=[('size',D),('guid',GUID),('devinst',D),('reserved',U)]
class InstallParams(C.Structure):
    _fields_=[('size',D),('flags',D),('flags_ex',D),('parent',P),('callback',P),('context',P),('queue',P),('class_reserved',U),('reserved',D),('path',C.c_wchar*260)]
class FileTime(C.Structure):
    _fields_=[('low',D),('high',D)]
class DriverInfo(C.Structure):
    _fields_=[('size',D),('type',D),('reserved',U),('description',C.c_wchar*256),('manufacturer',C.c_wchar*256),('provider',C.c_wchar*256),('date',FileTime),('version',C.c_uint64)]
class DriverParams(C.Structure):
    _fields_=[('size',D),('rank',D),('flags',D),('private',U),('reserved',D)]

@dataclass(frozen=True)
class TrustResult:
    verified: bool
    signer: str=''
    catalog: str=''
    files_verified: int=0
    reason: str=''
    def to_dict(self):return asdict(self)

from ..core.windows import dll, system_executable, function as _function

def verify_member(file:Path,catalog:Path)->bool:
    """Verify a SIP-aware member hash against this explicit signed catalog.

    SHA256 then SHA1; trust uses Windows cached revocation data only. Unknown
    revocation/trust fails closed. This makes no WHQL certification claim.
    """
    trust=dll('wintrust.dll'); kernel=dll('kernel32.dll')
    create=_function(kernel,'CreateFileW',[W,D,D,P,D,D,P],P)
    seek=_function(kernel,'SetFilePointerEx',[P,C.c_int64,P,D],C.c_int)
    close=_function(kernel,'CloseHandle',[P],C.c_int)
    acquire=_function(trust,'CryptCATAdminAcquireContext2',[C.POINTER(P),P,W,P,D],C.c_int)
    release=_function(trust,'CryptCATAdminReleaseContext',[P,D],C.c_int)
    calc=_function(trust,'CryptCATAdminCalcHashFromFileHandle2',[P,P,C.POINTER(D),P,D],C.c_int)
    verify=_function(trust,'WinVerifyTrust',[P,C.POINTER(GUID),C.POINTER(TrustData)],C.c_int32)
    handle=create(str(file),0x80000000,1,None,3,0x80,None)
    if handle in (None,C.c_void_p(-1).value):return False
    action=GUID.from_text('00AAC56B-CD44-11D0-8CC2-00C04FC295EE')
    try:
        for algorithm in ('SHA256','SHA1'):
            admin=P()
            if not acquire(C.byref(admin),None,algorithm,None,0):continue
            try:
                seek(handle,0,None,0)
                size=D()
                if not calc(admin,handle,C.byref(size),None,0) or not 0<size.value<=128:continue
                seek(handle,0,None,0)
                digest=(C.c_ubyte*size.value)()
                if not calc(admin,handle,C.byref(size),digest,0):continue
                tag=bytes(digest).hex().upper()
                cat=CatalogInfo(C.sizeof(CatalogInfo),0,str(catalog),tag,str(file),handle,C.cast(digest,P),size.value,None,admin)
                data=TrustData();data.size=C.sizeof(data);data.ui=2;data.choice=2;data.subject=C.cast(C.pointer(cat),P)
                data.state_action=1;data.flags=0x80|0x1000 # chain except root, cached only
                result=verify(None,C.byref(action),C.byref(data))
                data.state_action=2;verify(None,C.byref(action),C.byref(data))
                if result==0:return True
            finally:release(admin,0)
        return False
    finally:close(handle)

def verify_package(inf:Path,catalog_name:str)->TrustResult:
    if platform.system()!='Windows':raise UnsupportedPlatform('Native driver verification requires Windows')
    inf=Path(inf).resolve(strict=True)
    if inf.suffix.lower()!='.inf' or not inf.is_file():raise ValueError('Choose an INF file')
    if not catalog_name or Path(catalog_name).name!=catalog_name or any(c in catalog_name for c in '\\/:'):
        return TrustResult(False,reason='Missing or unsafe catalog filename')
    catalog=inf.parent/catalog_name
    if not catalog.is_file() or catalog.is_symlink():return TrustResult(False,reason='Catalog file is missing or linked')
    signer=Signer();signer.size=C.sizeof(signer)
    setup=dll('setupapi.dll'); verify=_function(setup,'SetupVerifyInfFileW',[W,P,C.POINTER(Signer)],C.c_int)
    if not verify(str(inf),None,C.byref(signer)):
        return TrustResult(False,reason=f'SetupAPI rejected INF signature (0x{C.get_last_error():08x})')
    count=0
    for path in sorted(inf.parent.rglob('*')):
        if path.is_symlink() or getattr(path.stat(),'st_file_attributes',0)&0x400:
            return TrustResult(False,reason='Package contains a link or reparse point')
        if not path.is_file() or path.suffix.lower()=='.cat':continue
        if not verify_member(path,catalog):
            return TrustResult(False,signer.signer,str(catalog),count,f'Catalog membership/trust rejected: {path.name}')
        count+=1
    if not count:return TrustResult(False,reason='No catalog members verified')
    return TrustResult(True,signer.signer,str(catalog),count,'Windows INF signature and all payload catalog memberships verified; cached trust policy')

def compatible_drivers(inf:Path,instance_id:str)->list[dict]:
    """Let SetupAPI choose valid model/OS decorations for the current device."""
    setup=dll('setupapi.dll'); path=str(Path(inf).resolve(strict=True))
    if len(path)>=260:raise ValueError('INF path exceeds supported native inspection length')
    create=_function(setup,'SetupDiCreateDeviceInfoList',[P,P],P)
    destroy=_function(setup,'SetupDiDestroyDeviceInfoList',[P],C.c_int)
    opened=_function(setup,'SetupDiOpenDeviceInfoW',[P,W,P,D,C.POINTER(DeviceInfo)],C.c_int)
    get=_function(setup,'SetupDiGetDeviceInstallParamsW',[P,C.POINTER(DeviceInfo),C.POINTER(InstallParams)],C.c_int)
    put=_function(setup,'SetupDiSetDeviceInstallParamsW',[P,C.POINTER(DeviceInfo),C.POINTER(InstallParams)],C.c_int)
    build=_function(setup,'SetupDiBuildDriverInfoList',[P,C.POINTER(DeviceInfo),D],C.c_int)
    enum=_function(setup,'SetupDiEnumDriverInfoW',[P,C.POINTER(DeviceInfo),D,D,C.POINTER(DriverInfo)],C.c_int)
    rank=_function(setup,'SetupDiGetDriverInstallParamsW',[P,C.POINTER(DeviceInfo),C.POINTER(DriverInfo),C.POINTER(DriverParams)],C.c_int)
    handle=create(None,None)
    if handle in (None,C.c_void_p(-1).value):raise OSError('SetupAPI device list unavailable')
    try:
        device=DeviceInfo();device.size=C.sizeof(device)
        params=InstallParams();params.size=C.sizeof(params)
        if not opened(handle,instance_id,None,0,C.byref(device)) or not get(handle,C.byref(device),C.byref(params)):
            raise OSError('Device is unavailable for native compatibility review')
        params.flags|=0x10000 # DI_ENUMSINGLEINF, no installation request
        params.path=path
        if not put(handle,C.byref(device),C.byref(params)) or not build(handle,C.byref(device),2):
            raise OSError(f'Native compatible driver list failed (0x{C.get_last_error():08x})')
        result=[]
        for index in range(100):
            info=DriverInfo();info.size=C.sizeof(info)
            if not enum(handle,C.byref(device),2,index,C.byref(info)):
                error=C.get_last_error()
                if error==259:break
                raise OSError(f'Native driver enumeration failed (0x{error:08x})')
            details=DriverParams();details.size=C.sizeof(details)
            if not rank(handle,C.byref(device),C.byref(info),C.byref(details)):raise OSError('Native rank unavailable')
            version='.'.join(str((info.version>>shift)&65535) for shift in (48,32,16,0))
            result.append({'description':info.description,'manufacturer':info.manufacturer,'provider':info.provider,'version':version,'native_rank':details.rank})
        return sorted(result,key=lambda x:x['native_rank'])
    finally:destroy(handle)
