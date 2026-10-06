import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from smart_os.core.readiness import evaluate,dual_boot_readiness
from smart_os.driver_engine.inventory import Device
from smart_os.driver_engine.machine_profile import export_profile,load_profile,MachineProfileError

class ReadinessTests(unittest.TestCase):
    def test_encrypted_volume_always_requires_review(self):
        r=evaluate({'boot_mode':'Uefi','fast_startup':0,'bitlocker':[{'mount':'C:','protection':'On','volume':'FullyEncrypted','lock':'Unlocked'}]})
        self.assertEqual(r['checks'][2]['state'],'review'); self.assertFalse(r['automatic_changes']); self.assertFalse(r['ready_to_partition'])
    def test_missing_privileges_never_claim_encryption_disabled(self):
        r=evaluate({'boot_mode':'unknown','fast_startup':None,'bitlocker':None})
        self.assertEqual(r['checks'][1]['state'],'unknown'); self.assertEqual(r['checks'][2]['state'],'unknown')
    def test_fast_startup_and_non_windows_block_readiness(self):
        self.assertEqual(evaluate({'fast_startup':1})['checks'][1]['state'],'review')
        with patch('smart_os.core.readiness.platform.system',return_value='Linux'),patch('smart_os.core.readiness.powershell') as ps:
            self.assertFalse(dual_boot_readiness()['ready_to_partition']); ps.assert_not_called()

class OfflineProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup); self.path=Path(self.temp.name)/'machine.json'
        self.devices=[Device('PRIVATE-SERIAL','Wi-Fi','OEM','Net',('PCI\\VEN_1234&DEV_5678',),('PCI\\CC_0280',),28)]
    def test_round_trip_no_instance_ids_and_no_overwrite(self):
        with patch('smart_os.driver_engine.machine_profile.platform.machine',return_value='AMD64'):export_profile(self.path,self.devices)
        self.assertNotIn('PRIVATE-SERIAL',self.path.read_text()); self.assertEqual(load_profile(self.path)[0].hardware_ids,self.devices[0].hardware_ids)
        with self.assertRaises(MachineProfileError):export_profile(self.path,self.devices)
    def test_foreign_architecture_rejected(self):
        with patch('smart_os.driver_engine.machine_profile.platform.machine',return_value='ARM64'):export_profile(self.path,self.devices)
        with self.assertRaises(MachineProfileError):load_profile(self.path)
    def test_malformed_identifiers_rejected(self):
        with patch('smart_os.driver_engine.machine_profile.platform.machine',return_value='AMD64'):export_profile(self.path,self.devices)
        data=json.loads(self.path.read_text()); data['devices'][0]['hardware_ids']='PCI\\anything'; self.path.write_text(json.dumps(data))
        with self.assertRaises(MachineProfileError):load_profile(self.path)
