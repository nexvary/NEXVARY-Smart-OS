"""Fixed Windows servicing operations through Microsoft's installed DISM."""
from __future__ import annotations
import ctypes
import os
import platform
import subprocess
from pathlib import Path
from ..core.process import OperationError, UnsupportedPlatform, run


def _dism(arguments: list[str]) -> dict:
    if platform.system() != 'Windows':
        raise UnsupportedPlatform('DISM inspection requires Windows 10/11 x64')
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise OperationError('DISM inspection requires administrator permission. No changes were made.')
    from ..core.windows import system_executable
    executable = system_executable('dism.exe')
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


def scan_health() -> dict:
    result = _execute('ScanHealth', ['/Online', '/Cleanup-Image', '/ScanHealth'], False)
    output = result.get('output', '').casefold()
    result['health_state'] = ('healthy' if 'no component store corruption detected' in output else
                              'non-repairable' if 'cannot be repaired' in output else
                              'repairable' if 'component store is repairable' in output else 'unknown')
    return result


def analyze_store() -> dict:
    return _execute('AnalyzeComponentStore', ['/Online', '/Cleanup-Image', '/AnalyzeComponentStore'], False)


def _execute(operation: str, arguments: list[str], changes: bool) -> dict:
    if platform.system() != 'Windows':
        raise UnsupportedPlatform('Windows servicing requires Windows')
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise OperationError('Administrator permission is required')
    from ..core.windows import system_executable
    argv = [system_executable('dism.exe'), '/English', *arguments, '/NoRestart']
    try:
        completed = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8',
                                   errors='replace', timeout=1800, shell=False,
                                   creationflags=0x08000000 if os.name == 'nt' else 0)
    except subprocess.TimeoutExpired:
        # A timed-out repair may already have changed components. Never retry silently.
        return {'operation': operation, 'changes_requested': changes, 'status': 'indeterminate',
                'reboot_required': None, 'verification': 'not-run',
                'message': 'DISM exceeded 30 minutes. Inspect Windows/Logs/DISM/dism.log before retrying.'}
    code = completed.returncode & 0xffffffff
    result = {'tool': 'Microsoft DISM', 'operation': operation, 'changes_requested': changes,
              'exit_code': code, 'exit_code_hex': f'0x{code:08X}',
              'status': 'completed' if code in (0, 3010) else 'failed',
              'reboot_required': code == 3010, 'output': completed.stdout.strip()[-60000:],
              'error_output': completed.stderr.strip()[-10000:], 'automatic_reboot': False}
    if code not in (0, 3010):
        result['suggestion'] = ('Repair source files were not found. Use a matching Windows repair source.'
                                if code == 0x800f081f else 'Inspect the DISM log and exit code; no automatic retry.')
    return result


def restore_health(source: Path | None = None, *, confirmed: bool = False) -> dict:
    if confirmed is not True:
        raise ValueError('Explicit repair confirmation is required')
    arguments = ['/Online', '/Cleanup-Image', '/RestoreHealth']
    if source is not None:
        source = Path(source).resolve(strict=True)
        if not source.is_dir() or source.is_symlink() or not (source / 'WinSxS').is_dir():
            raise ValueError('Select the Windows folder of a matching mounted repair image, containing WinSxS')
        arguments += [f'/Source:{source}', '/LimitAccess']
    result = _execute('RestoreHealth', arguments, True)
    result['source'] = 'local Windows repair folder' if source is not None else 'Windows configured repair source / Windows Update'
    result['verification'] = 'not-run'
    if result['status'] == 'completed' and not result['reboot_required']:
        followup = scan_health()
        result['verification'] = followup
        if followup['status'] != 'completed' or followup['health_state'] in {'repairable','non-repairable'}:
            result['status'] = 'verification-failed'
        result['health_verified'] = followup['health_state'] == 'healthy' and followup['status'] == 'completed'
    return result


def cleanup_store(*, confirmed: bool = False) -> dict:
    if confirmed is not True:
        raise ValueError('Explicit component cleanup confirmation is required')
    before = analyze_store()
    if before['status'] != 'completed':
        return {'operation': 'StartComponentCleanup', 'status': 'blocked', 'changes_requested': False,
                'reason': 'Component store analysis failed', 'analysis': before}
    result = _execute('StartComponentCleanup', ['/Online', '/Cleanup-Image', '/StartComponentCleanup'], True)
    result['analysis_before'] = before
    result['reset_base'] = False
    if result['status'] == 'completed' and not result['reboot_required']:
        result['analysis_after'] = analyze_store()
    return result
