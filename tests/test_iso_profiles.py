import io
from pathlib import Path
import tempfile
import unittest
import pycdlib
import yaml
from smart_os.installer_engine.iso import analyze, sha256, ISOError
from smart_os.installer_engine.profiles import InstallationProfile
from smart_os.distro_adapters.config import generate, AdapterError

def make_iso(path,distribution='debian',live=False):
    iso=pycdlib.PyCdlib(); iso.new(interchange_level=3,rock_ridge='1.09'); iso.add_directory(iso_path='/DOTDISK',rr_name='.disk')
    label=f'{distribution.title()} GNU/Linux amd64 test-only fixture'.encode(); iso.add_fp(io.BytesIO(label),len(label),iso_path='/DOTDISK/INFO.;1',rr_name='info')
    if distribution=='ubuntu':
        iso.add_directory(iso_path='/CASPER',rr_name='casper'); value=b'id: ubuntu-server'; iso.add_fp(io.BytesIO(value),len(value),iso_path='/CASPER/SOURCES.YML;1',rr_name='install-sources.yaml')
    else:
        directory='LIVE' if live else 'INSTALL'; rr='live' if live else 'install.amd'; iso.add_directory(iso_path='/'+directory,rr_name=rr); iso.add_fp(io.BytesIO(b'fixture'),7,iso_path='/'+directory+'/VMLINUX.;1',rr_name='vmlinuz')
    iso.add_directory(iso_path='/EFI',rr_name='EFI'); iso.add_directory(iso_path='/EFI/BOOT',rr_name='BOOT'); iso.add_fp(io.BytesIO(b'not-signed'),10,iso_path='/EFI/BOOT/BOOTX64.EFI;1',rr_name='BOOTX64.EFI'); iso.write(str(path)); iso.close()
class ISOTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
    def tearDown(self):self.temp.cleanup()
    def test_three_structures_config_and_original_immutable(self):
        for distro in ['debian','kali','ubuntu']:
            path=self.root/(distro+'.iso'); make_iso(path,distro); before=path.read_bytes(); report=analyze(path,sha256(path))
            self.assertEqual(report.distribution,distro); self.assertEqual(report.architecture,'amd64'); self.assertTrue(report.uefi); name,content=generate(InstallationProfile(distro),report); self.assertEqual(path.read_bytes(),before); self.assertNotIn('partman/confirm',content)
            if distro=='ubuntu':self.assertIn('storage',yaml.safe_load(content)['autoinstall']['interactive-sections'])
    def test_hash_mismatch(self):
        path=self.root/'a.iso'; make_iso(path)
        with self.assertRaises(ISOError):analyze(path,'0'*64)
    def test_malformed_hash(self):
        path=self.root/'a.iso'; make_iso(path)
        with self.assertRaises(ISOError):analyze(path,'oops')
    def test_corrupt_iso(self):
        path=self.root/'fake.iso'; path.write_bytes(b'not an iso')
        with self.assertRaises(ISOError):analyze(path)
    def test_filename_not_distribution_evidence(self):
        path=self.root/'Ubuntu.iso'; make_iso(path,'debian'); self.assertEqual(analyze(path).distribution,'debian')
    def test_live_kali_seed_blocked(self):
        path=self.root/'live.iso'; make_iso(path,'kali',True)
        with self.assertRaises(AdapterError):generate(InstallationProfile('kali'),analyze(path,sha256(path)))
    def test_unverified_seed_blocked(self):
        path=self.root/'a.iso'; make_iso(path)
        with self.assertRaises(AdapterError):generate(InstallationProfile('debian'),analyze(path))
    def test_profile_roundtrip_without_password(self):
        p=InstallationProfile('ubuntu'); path=self.root/'p.json'; p.save(path); self.assertEqual(p,InstallationProfile.load(path)); self.assertNotIn('password',path.read_text())
    def test_untrusted_fields_rejected(self):
        for values in [{'hostname':'x\n; rm -rf /'},{'username':'root'},{'keyboard':'us;touch /tmp/a'},{'locale':'x\nd-i evil'},{'timezone':'no/such-zone'},{'preset':'random'},{'schema_version':99}]:
            with self.subTest(values=values),self.assertRaises(ValueError):InstallationProfile('debian',**values).validate()
