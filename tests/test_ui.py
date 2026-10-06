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

    def test_language_switch_keeps_profile_and_iso_selection(self):
        w=LinuxWindow('en'); w.fields['hostname'].setText('my-workstation'); w.iso_path.setText('C:/images/debian.iso'); w.expected_hash.setText('a'*64); w.navigate(3)
        w.change_language(1)
        self.assertEqual(w.fields['hostname'].text(),'my-workstation'); self.assertEqual(w.iso_path.text(),'C:/images/debian.iso'); self.assertEqual(w.expected_hash.text(),'a'*64); self.assertEqual(w.stack.currentIndex(),3); w.close()
    def test_device_search_status_and_network_filters(self):
        from smart_os.driver_engine.inventory import Device
        w=DriverWindow('en'); w.devices=[Device('id','Wireless','Intel','Net',('PCI\\VEN_8086',),(),28),Device('id2','Audio','OEM','Media',('HDAUDIO\\A',),(),0,'oem1.inf')]; w.render_devices()
        w.device_search.setText('8086'); self.assertFalse(w.device_table.isRowHidden(0)); self.assertTrue(w.device_table.isRowHidden(1))
        w.device_search.clear(); w.device_filter.setCurrentIndex(3); self.assertFalse(w.device_table.isRowHidden(0)); self.assertTrue(w.device_table.isRowHidden(1))
        w.device_filter.setCurrentIndex(2); self.assertTrue(w.device_table.isRowHidden(0)); self.assertTrue(w.device_table.isRowHidden(1)); w.close()
    def test_report_escapes_untrusted_html(self):
        from smart_os.ui.panels import ReportPanel
        p=ReportPanel('ar'); p.display({'name':'<img src="file:///private">','hardware_ids':['PCI\\ID']})
        self.assertIn('<img src=',p.toPlainText()); self.assertNotIn('<img src="file:',p.toHtml()); p.close()
    def test_home_text_fits_minimum_window_in_both_languages(self):
        from PySide6.QtWidgets import QLabel
        for cls in (LinuxWindow,DriverWindow):
            for language in ('en','ar'):
                w=cls(language); w.resize(1000,700); w.show(); self.app.processEvents()
                for label in w.stack.currentWidget().findChildren(QLabel):
                    if label.isVisible() and label.wordWrap():self.assertLessEqual(label.heightForWidth(label.width()),label.height()+2,label.text())
                w.close()
    def test_bundled_font_has_arabic_latin_and_digits(self):
        from PySide6.QtGui import QRawFont
        glyphs=QRawFont.fromFont(self.app.font()).glyphIndexesForString('NEXVARY العربية 0123456789')
        self.assertTrue(glyphs); self.assertNotIn(0,glyphs)
    def test_device_details_do_not_use_space_before_selection(self):
        from smart_os.driver_engine.inventory import Device
        w=DriverWindow('en'); self.assertTrue(w.device_panel.isHidden())
        w.devices=[Device('id','Wi-Fi','OEM','Net',('PCI\\VEN_1234',),(),28)]; w.render_devices(); w.device_table.selectRow(0)
        self.assertFalse(w.device_panel.isHidden()); self.assertIn('Wi-Fi',w.device_panel.toPlainText()); w.close()
