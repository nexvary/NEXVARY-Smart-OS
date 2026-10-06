import unittest
from PySide6.QtCore import Qt
from smart_os.ui.common import application
from smart_os.linux_app import LinuxWindow
from smart_os.windows_app import DriverWindow
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=application()
    def test_independent_apps_and_reachable_pages(self):
        for cls in [LinuxWindow,DriverWindow]:
            w=cls(); self.assertEqual(w.stack.count(),6)
            for i in range(6):w.nav[i].click(); self.assertEqual(w.stack.currentIndex(),i)
            w.close()
    def test_arabic_rtl_technical_ltr(self):
        w=LinuxWindow('ar'); self.assertEqual(w.layoutDirection(),Qt.RightToLeft); self.assertEqual(w.expected_hash.layoutDirection(),Qt.LeftToRight); self.assertEqual(w.iso_path.layoutDirection(),Qt.LeftToRight); w.close()
    def test_language_switch_retains_inventory(self):
        from smart_os.driver_engine.inventory import Device
        w=DriverWindow(); w.devices=[Device('id','Test','OEM','Net',('ID',),(),28)]; w.render_devices(); w.change_language(1); self.assertEqual(w.device_table.rowCount(),1); self.assertEqual(w.layoutDirection(),Qt.RightToLeft); w.close()
