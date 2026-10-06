import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from smart_os.driver_engine import servicing
from smart_os.core.process import UnsupportedPlatform, OperationError

class ServicingTests(unittest.TestCase):
    def test_non_windows_never_executes(self):
        with patch.object(servicing.platform,'system',return_value='Linux'), patch.object(servicing,'run') as command:
            with self.assertRaises(UnsupportedPlatform):servicing.check_health()
            command.assert_not_called()
    def test_permission_failure_never_executes(self):
        native=Mock(); native.shell32.IsUserAnAdmin.return_value=0
        with patch.object(servicing.platform,'system',return_value='Windows'), patch.object(servicing.ctypes,'windll',native,create=True), patch.object(servicing,'run') as command:
            with self.assertRaises(OperationError):servicing.list_drivers()
            command.assert_not_called()
    def test_health_and_drivers_only_inspect(self):
        native=Mock(); native.shell32.IsUserAnAdmin.return_value=1
        with patch.object(servicing.platform,'system',return_value='Windows'), patch.object(servicing.ctypes,'windll',native,create=True), patch('smart_os.core.windows.system_executable',return_value='C:/Windows/System32/dism.exe'), patch.object(servicing,'run',return_value='real command output') as command:
            health=servicing.check_health(); drivers=servicing.list_drivers()
            self.assertFalse(health['changes_requested']); self.assertFalse(drivers['changes_requested'])
            self.assertEqual(command.call_args_list[0].args[0][1:],['/English','/Online','/Cleanup-Image','/CheckHealth'])
            self.assertEqual(command.call_args_list[1].args[0][1:],['/English','/Online','/Get-Drivers','/Format:Table'])
    def test_image_path_is_one_argument_and_not_mounted(self):
        with tempfile.TemporaryDirectory() as folder:
            image=Path(folder)/'image with spaces & input.wim'; image.write_bytes(b'test fixture')
            with patch.object(servicing,'_dism',return_value={}) as command:
                servicing.image_info(image)
                self.assertEqual(command.call_args.args[0],['/Get-WimInfo',f'/WimFile:{image.resolve()}'])
            with self.assertRaises(ValueError):servicing.image_info(Path(folder))
            image.rename(image.with_suffix('.exe'))
            with self.assertRaises(ValueError):servicing.image_info(image.with_suffix('.exe'))
