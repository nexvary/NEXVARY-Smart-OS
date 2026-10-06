"""Read-only Windows servicing through Microsoft's installed DISM.

No Dism++ binary or code is redistributed. No repair, cleanup, mount, driver
installation or removal command is exposed by this adapter.
"""
from __future__ import annotations
import ctypes
import os
import platform
from pathlib import Path
from ..core.process import OperationError, UnsupportedPlatform, run


def _dism(arguments: list[str]) -> dict:
    if platform.system() != 'Windows':
        raise UnsupportedPlatform('DISM inspection requires Windows 10/11 x64')
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise OperationError('DISM inspection requires administrator permission. No changes were made.')
    executable = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32' / 'dism.exe'
    output = run([str(executable), '/English', *arguments], timeout=180)
    return {'tool': 'Microsoft DISM', 'operation': arguments[1] if arguments[0] == '/Online' else arguments[0],
            'changes_requested': False, 'output': output.strip()}


def check_health() -> dict:
    """Read existing corruption flags; this does not perform a fresh ScanHealth."""
    result = _dism(['/Online', '/Cleanup-Image', '/CheckHealth'])
    result['operation'] = 'CheckHealth'
    result['scope'] = 'Existing corruption flags only; not a full scan or repair'
    return result


def list_drivers() -> dict:
    return _dism(['/Online', '/Get-Drivers', '/Format:Table'])


def image_info(path: Path) -> dict:
    path = Path(path).resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in {'.wim', '.esd'}:
        raise ValueError('Select an existing WIM or ESD file')
    return _dism(['/Get-WimInfo', f'/WimFile:{path}'])
