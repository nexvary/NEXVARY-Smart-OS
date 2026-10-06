from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from smart_os.driver_engine.inventory import Device, inventory
from smart_os.driver_engine.matching import Candidate, rank, parse_inf
from smart_os.driver_engine.backup import backup, verify_backup, DriverSafetyError
from smart_os.installer_engine.iso import sha256
from smart_os.core.process import UnsupportedPlatform, json_rows, ps_literal
class DriverTests(unittest.TestCase):
    def setUp(self):
        self.device=Device('private-id','Wi-Fi','Intel','Net',('PCI\\VEN_8086&DEV_1234&SUBSYS_00000001',),('PCI\\VEN_8086&DEV_1234',),28); self.exact=Candidate('d.inf',self.device.hardware_ids,'amd64','d.cat','Intel','1',True,True)
    def test_unmatched_never_eligible(self):
        r=rank(self.device,[replace(self.exact,hardware_ids=('PCI\\VEN_FFFF&DEV_FFFF',))])[0]; self.assertFalse(r.eligible); self.assertEqual(r.score,0)
    def test_unsigned_not_eligible(self):self.assertFalse(rank(self.device,[replace(self.exact,signature_verified=False)])[0].eligible)
    def test_wrong_architecture_not_eligible(self):self.assertFalse(rank(self.device,[replace(self.exact,architecture='arm64')])[0].eligible)
    def test_exact_outranks_new_generic(self):
        generic=replace(self.exact,hardware_ids=self.device.compatible_ids,version='999999'); ranked=rank(self.device,[generic,self.exact]); self.assertEqual(ranked[0].candidate,self.exact); self.assertFalse(ranked[1].eligible)
    def test_newer_date_not_preferred(self):
        self.assertEqual(rank(self.device,[replace(self.exact,version='1/1/2000,1.0')])[0].score,rank(self.device,[replace(self.exact,version='1/1/2026,999')])[0].score)
    def test_problem_codes_distinct(self):
        self.assertEqual(self.device.status,'missing'); self.assertEqual(replace(self.device,problem_code=10).status,'needs-review'); self.assertEqual(replace(self.device,problem_code=0,driver_inf='oem1.inf').status,'installed')
    def test_inf_comments_not_hardware_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'driver.inf'; p.write_text('[Version]\nCatalogFile=d.cat\nProvider=Intel\n[Models.NTamd64]\n%x%=Install,PCI\\VEN_8086&DEV_1234&SUBSYS_00000001\n; %evil%=Install,PCI\\VEN_FFFF\n'); c=parse_inf(p); self.assertEqual(c.hardware_ids,self.device.hardware_ids); self.assertFalse(c.signature_verified)
    def test_catalog_traversal(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'driver.inf'; p.write_text('[Version]\nCatalogFile=../evil.cat\n')
            with self.assertRaises(ValueError):parse_inf(p)
    def test_backup_tamper_detection(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); p=root/'d.inf'; p.write_bytes(b'driver'); m={'schema_version':1,'kind':'smart-driver-backup','files':{'d.inf':sha256(p)}}; (root/'smart-driver-manifest.json').write_text(json.dumps(m)); self.assertEqual(verify_backup(root),[p]); p.write_bytes(b'evil')
            with self.assertRaises(DriverSafetyError):verify_backup(root)
    def test_backup_path_escape(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'backup').mkdir(); (root/'secret').write_bytes(b'x'); m={'schema_version':1,'kind':'smart-driver-backup','files':{'../secret':sha256(root/'secret')}}; (root/'backup'/'smart-driver-manifest.json').write_text(json.dumps(m))
            with self.assertRaises(DriverSafetyError):verify_backup(root/'backup')
    def test_linux_inventory_not_faked(self):
        with patch('smart_os.driver_engine.inventory.platform.system',return_value='Linux'):
            with self.assertRaises(UnsupportedPlatform):inventory()
    def test_inf_injection_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(DriverSafetyError):backup(Path(t)/'b','oem1.inf & shutdown /s')
    def test_json_shapes(self):self.assertEqual(json_rows('{"a":1}'),[{'a':1}]); self.assertEqual(json_rows('[]'),[])
    def test_ps_literal(self):self.assertEqual(ps_literal("a'b;$(evil)"),"'a''b;$(evil)'")
