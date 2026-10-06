"""System32-only Win32 loading and executable resolution."""
import ctypes as C
import platform
from pathlib import Path
from .process import UnsupportedPlatform
D=C.c_uint32; P=C.c_void_p; W=C.c_wchar_p

def dll(name):
    if platform.system()!='Windows':raise UnsupportedPlatform('This operation requires Windows')
    return C.WinDLL(name,use_last_error=True,winmode=0x800)

def function(lib,name,args,result):
    f=getattr(lib,name);f.argtypes=args;f.restype=result;return f

def system_executable(name):
    if name not in {'pnputil.exe','dism.exe','powershell.exe'}:raise ValueError('Unsupported system executable')
    f=function(dll('kernel32.dll'),'GetSystemDirectoryW',[W,D],D)
    buf=C.create_unicode_buffer(32768);length=f(buf,len(buf))
    if not length or length>=len(buf):raise OSError('Cannot locate Windows system directory')
    return str(Path(buf.value)/('WindowsPowerShell/v1.0/powershell.exe' if name=='powershell.exe' else name))
