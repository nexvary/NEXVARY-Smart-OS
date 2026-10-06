from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from smart_os.driver_engine.inventory import Device
from smart_os.driver_engine import preflight, native
from smart_os.driver_engine.native import TrustResult
from smart_os.core.elevation import validate_request, dispatch
from smart_os.core.process import UnsupportedPlatform

class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.inf=Path(self.temp.name)/'driver.inf'
        self.inf.write_text('[Version]\nCatalogFile=driver.cat\n[Models.NTamd64]\n%Device%=Install,PCI\\VEN_1234&DEV_5678\n')
        self.device=Device('real-local-id','Wi-Fi','OEM','Net',('PCI\\VEN_1234&DEV_5678',),(),28)
    def test_unmatched_stops_before_native_verification(self):
        with patch.object(preflight,'verify_package') as verify:
            r=preflight.review_driver(self.inf,replace(self.device,hardware_ids=('USB\\VID_9999',)))
            self.assertFalse(r['preflight_passed']);verify.assert_not_called()
    def test_untrusted_stops_before_compatibility(self):
        with patch.object(preflight,'verify_package',return_value=TrustResult(False,reason='Tampered package')),patch.object(preflight,'compatible_drivers') as compatible:
            r=preflight.review_driver(self.inf,self.device)
            self.assertFalse(r['preflight_passed']);compatible.assert_not_called()
    def test_native_os_rejection_blocks_plan(self):
        with patch.object(preflight,'verify_package',return_value=TrustResult(True)),patch.object(preflight,'compatible_drivers',return_value=[]):
            self.assertFalse(preflight.review_driver(self.inf,self.device)['preflight_passed'])
    def test_compatible_id_only_requires_oem_review(self):
        with patch.object(preflight,'verify_package',return_value=TrustResult(True)),patch.object(preflight,'compatible_drivers',return_value=[{'native_rank':1}]):
            device=replace(self.device,hardware_ids=('PCI\\VEN_1234&DEV_5678&SUBSYS_1111',),compatible_ids=self.device.hardware_ids)
            self.assertFalse(preflight.review_driver(self.inf,device)['preflight_passed'])
    def test_sensitive_classes_blocked_and_never_installable(self):
        with patch.object(preflight,'verify_package',return_value=TrustResult(True)),patch.object(preflight,'compatible_drivers',return_value=[{'native_rank':1}]):
            for name in ('Firmware','System','SCSIAdapter','HDC','SecurityDevices'):
                r=preflight.review_driver(self.inf,replace(self.device,class_name=name))
                self.assertFalse(r['preflight_passed']);self.assertEqual(r['installation'],'blocked-in-alpha')
    def test_review_digest_binds_payload_and_device_and_remains_gated(self):
        with patch.object(preflight,'verify_package',return_value=TrustResult(True)),patch.object(preflight,'compatible_drivers',return_value=[{'native_rank':1}]):
            a=preflight.review_driver(self.inf,self.device)
            self.assertTrue(a['preflight_passed']);self.assertEqual(a['installation'],'blocked-in-alpha');self.assertNotIn('commands',a)
            b=preflight.review_driver(self.inf,replace(self.device,instance_id='different-local-id'))
            self.assertNotEqual(a['plan_digest'],b['plan_digest'])
            (self.inf.parent/'payload.sys').write_bytes(b'mutated')
            self.assertNotEqual(a['plan_digest'],preflight.review_driver(self.inf,self.device)['plan_digest'])
    def test_native_calls_reject_non_windows(self):
        with patch.object(native.platform,'system',return_value='Linux'):
            with self.assertRaises(UnsupportedPlatform):native.verify_package(self.inf,'driver.cat')
            with self.assertRaises(UnsupportedPlatform):native.compatible_drivers(self.inf,self.device.instance_id)

class PrivilegeProtocolTests(unittest.TestCase):
    def request(self,op='check-health',params=None):
        return {'schema':1,'nonce':'a'*32,'operation':op,'parameters':params or {}}
    def test_only_fixed_operations_and_keys(self):
        for op in ('install-driver','delete-driver','run','powershell','reboot','restore-health'):
            with self.assertRaises(ValueError):validate_request(self.request(op))
        with self.assertRaises(ValueError):validate_request(self.request(params={'script':'Write-Host unsafe'}))
        with self.assertRaises(ValueError):validate_request(self.request()|{'executable':'bad.exe'})
    def test_bad_nonce_and_schema_rejected(self):
        for r in (self.request()|{'nonce':'../x'},self.request()|{'schema':2},None):
            with self.assertRaises(ValueError):validate_request(r)
    def test_paths_and_inf_arguments_validated(self):
        with self.assertRaises(ValueError):validate_request(self.request('image-info',{'path':'relative.wim'}))
        for inf in ('oem1.inf & shutdown /s','../oem1.inf','driver.inf'):
            with self.assertRaises(ValueError):validate_request(self.request('driver-backup',{'destination':str(Path('/').resolve()),'inf':inf}))
        self.assertEqual(validate_request(self.request('driver-backup',{'destination':str(Path('/').resolve()),'inf':'oem12.inf'}))['parameters']['inf'],'oem12.inf')
    def test_oversize_or_nul_rejected(self):
        for path in ('/path\0evil','/'+('a'*33000)):
            with self.assertRaises(ValueError):validate_request(self.request('image-info',{'path':path}))
    def test_dispatch_never_interprets_commands(self):
        with patch('smart_os.driver_engine.servicing.check_health',return_value={'changes_requested':False}) as operation:
            self.assertFalse(dispatch(self.request())['changes_requested']);operation.assert_called_once_with()
