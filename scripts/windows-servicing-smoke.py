"""Real servicing on the disposable CI Windows machine, never a user's PC."""
import json
from pathlib import Path
from smart_os.core.elevation import request_operation
from smart_os.core.logging import export_report

report = {'environment': 'disposable Windows Server 2022 CI runner',
          'interactive_uac_tested': False, 'physical_windows10_11_tested': False,
          'driver_installation_tested': False, 'operations': {}}
try:
    for op, params in [('scan-health', {}), ('analyze-store', {}),
                       ('restore-health', {'confirmed': True, 'source': None}),
                       ('cleanup-store', {'confirmed': True})]:
        result = request_operation(op, params)
        report['operations'][op] = result
        print(f"{op}: {result.get('status')}, exit={result.get('exit_code_hex')}, reboot={result.get('reboot_required')}", flush=True)
        assert result['status'] == 'completed', f'{op} did not complete; inspect the verification artifact'
        assert not result['automatic_reboot']
        if op == 'restore-health' and not result['reboot_required']:
            assert result['health_verified'], 'RestoreHealth did not produce a confirmed healthy scan'
        if op == 'cleanup-store':
            assert result['reset_base'] is False
    report['verification'] = 'passed'
finally:
    Path('artifacts/verification').mkdir(parents=True, exist_ok=True)
    export_report(Path('artifacts/verification/windows-servicing.json'), report)
