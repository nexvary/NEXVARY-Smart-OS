import subprocess
import json
import os
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from smart_os.driver_engine import servicing
from smart_os.core.elevation import validate_request, dispatch
from smart_os.windows_app import DriverWindow
from smart_os.ui.common import application
from PySide6.QtWidgets import QMessageBox


class ServicingExecutionTests(unittest.TestCase):
    def setUp(self):
        native=Mock(); native.shell32.IsUserAnAdmin.return_value=1
        for context in (patch.object(servicing.platform,'system',return_value='Windows'),
                        patch.object(servicing.ctypes,'windll',native,create=True),
                        patch('smart_os.core.windows.system_executable',return_value='C:/Windows/System32/dism.exe')):
            context.start();self.addCleanup(context.stop)
    def request(self,op,params):
        return {'schema':1,'nonce':'a'*32,'operation':op,'parameters':params}
    def test_unconfirmed_changes_cannot_start(self):
        with patch.object(servicing.subprocess,'run') as command:
            for operation in (servicing.restore_health,servicing.cleanup_store):
                for confirmation in (False,None,1,'true'):
                    with self.assertRaises(ValueError):operation(confirmed=confirmation)
            command.assert_not_called()
        for op,params in [('restore-health',{'confirmed':False,'source':None}),('cleanup-store',{'confirmed':1})]:
            with self.assertRaises(ValueError):validate_request(self.request(op,params))
    def test_repair_rechecks_health_without_shell_or_reboot(self):
        with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=0,stdout='Operation completed',stderr='')) as command:
            result=dispatch(self.request('restore-health',{'confirmed':True,'source':None}))
            self.assertEqual(result['status'],'completed');self.assertEqual(result['verification']['operation'],'ScanHealth')
            first=command.call_args_list[0];self.assertIn('/RestoreHealth',first.args[0]);self.assertIn('/NoRestart',first.args[0])
            self.assertFalse(first.kwargs['shell']);self.assertNotIn('/ResetBase',first.args[0])
    def test_reboot_required_is_success_but_not_verified_yet(self):
        with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=3010,stdout='Restart needed',stderr='')) as command:
            result=servicing.restore_health(confirmed=True)
            self.assertEqual(result['status'],'completed');self.assertTrue(result['reboot_required']);self.assertEqual(result['verification'],'not-run');self.assertEqual(command.call_count,1)
    def test_failure_and_timeout_do_not_retry_or_claim_success(self):
        with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=-2146498529,stdout='Failed',stderr='')) as command:
            result=servicing.restore_health(confirmed=True)
            self.assertEqual(result['status'],'failed');self.assertEqual(result['exit_code_hex'],'0x800F081F');self.assertEqual(command.call_count,1)
        with patch.object(servicing.subprocess,'run',side_effect=subprocess.TimeoutExpired('dism',1800)):
            result=servicing.restore_health(confirmed=True);self.assertEqual(result['status'],'indeterminate');self.assertTrue(result['changes_requested'])
    def test_local_source_is_one_argument_and_disables_downloads(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'Windows & source';(source/'WinSxS').mkdir(parents=True)
            with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=3010,stdout='OK',stderr='')) as command:
                servicing.restore_health(source,confirmed=True)
                self.assertIn(f'/Source:{source.resolve()}',command.call_args.args[0]);self.assertIn('/LimitAccess',command.call_args.args[0])
            with self.assertRaises(ValueError):servicing.restore_health(Path(folder),confirmed=True)
    def test_cleanup_requires_analysis_and_never_resetbase(self):
        with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=0,stdout='Analysis/cleanup',stderr='')) as command:
            result=servicing.cleanup_store(confirmed=True)
            self.assertEqual(command.call_count,3);self.assertIn('/AnalyzeComponentStore',command.call_args_list[0].args[0]);self.assertIn('/StartComponentCleanup',command.call_args_list[1].args[0]);self.assertFalse(result['reset_base'])
        with patch.object(servicing.subprocess,'run',return_value=Mock(returncode=5,stdout='',stderr='')) as command:
            self.assertEqual(servicing.cleanup_store(confirmed=True)['status'],'blocked');self.assertEqual(command.call_count,1)


class ServicingUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=application()
    def test_cancelled_cleanup_never_calls_helper(self):
        w=DriverWindow('ar')
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.No),patch.object(w,'async_task') as task:
            w.clean_components();task.assert_not_called()
        w.close()

    def test_repair_confirmation_and_source_cancel_never_run(self):
        w=DriverWindow('en')
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Cancel),patch.object(w,'async_task') as task:
            w.repair_windows();task.assert_not_called()
        with patch.object(QMessageBox,'question',return_value=QMessageBox.No),patch.object(QMessageBox,'warning',return_value=QMessageBox.No),patch.object(w,'async_task') as task:
            w.repair_windows();task.assert_not_called()
        w.close()
    def test_confirmed_cleanup_dispatches_fixed_operation(self):
        w=DriverWindow('ar')
        with patch.object(QMessageBox,'warning',return_value=QMessageBox.Yes),patch.object(w,'async_task') as task,patch('smart_os.windows_app.request_operation',return_value={}) as helper:
            w.clean_components();task.call_args.args[1]();helper.assert_called_once_with('cleanup-store',{'confirmed':True})
        w.close()


class ServicingEvidenceTests(unittest.TestCase):
    def test_native_smoke_writes_a_readable_report(self):
        script=Path(__file__).resolve().parents[1]/'scripts/windows-servicing-smoke.py'
        outcome={'status':'completed','exit_code_hex':'0x00000000','reboot_required':False,
                 'automatic_reboot':False,'health_verified':True,'reset_base':False}
        previous=Path.cwd()
        with tempfile.TemporaryDirectory() as folder, patch('smart_os.core.elevation.request_operation',return_value=outcome):
            try:
                os.chdir(folder);runpy.run_path(str(script))
                report=json.loads(Path('artifacts/verification/windows-servicing.json').read_text())
                self.assertEqual(report['verification'],'passed');self.assertEqual(len(report['operations']),4)
            finally:os.chdir(previous)
