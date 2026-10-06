from pathlib import Path
import tempfile
import unittest
from smart_os.core.download import validate_url
from smart_os.core.logging import Journal, redact
from smart_os.core.diagnostics import analyze_log
class CoreTests(unittest.TestCase):
    def test_official_https_only(self):
        validate_url('https://cdimage.debian.org/image.iso')
        for url in ['http://cdimage.debian.org/a','https://cdimage.debian.org.evil.com/a','https://localhost/a','https://evil.com/a','https://u:p@cdimage.debian.org/a','https://cdimage.debian.org:8443/a','file:///etc/passwd']:
            with self.subTest(url=url),self.assertRaises(ValueError):validate_url(url)
    def test_nested_identifier_redaction(self):
        r=redact({'password':'secret','serial':'123','devices':[{'hardware_ids':['private'],'instance_id':'private','name':'Wi-Fi'}]}); self.assertNotIn('private',str(r)); self.assertEqual(r['devices'][0]['name'],'Wi-Fi')
    def test_journal_secrets(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'log'; Journal(p).record('test','failed',password='unique-password',message='token=unique-token',serial='private-serial'); text=p.read_text(); self.assertNotIn('unique-',text); self.assertNotIn('private-serial',text)
    def test_error_classification_and_no_auto_repair(self):
        for text,code in [('GRUB installation failed','grub-failure'),('Temporary failure resolving archive.ubuntu.com','dns-failure'),('No space left on device','disk-full')]:self.assertEqual(analyze_log(text)[0].code,code)
        self.assertEqual(analyze_log('unrecognized message'),[]); self.assertTrue(all(not f.automatic_repair for f in analyze_log('GRUB failed and network timeout')))

class DownloadIntegrityTests(unittest.TestCase):
    def transfer(self,payload,digest,path,max_bytes=100):
        from unittest.mock import patch
        from smart_os.core.download import download_iso
        import io
        class Response(io.BytesIO):url='https://cdimage.debian.org/test.iso'
        class Opener:
            def open(self,*args,**kwargs):return Response(payload)
        with patch('smart_os.core.download.build_opener',return_value=Opener()):return download_iso(Response.url,digest,path,max_bytes)
    def test_verified_transfer_and_no_overwrite(self):
        import hashlib
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'image.iso'; self.transfer(b'example',hashlib.sha256(b'example').hexdigest(),p); self.assertEqual(p.read_bytes(),b'example')
            with self.assertRaises(ValueError):self.transfer(b'example',hashlib.sha256(b'example').hexdigest(),p)
    def test_mismatch_leaves_no_completed_or_partial_file(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'image.iso'
            with self.assertRaises(ValueError):self.transfer(b'example','0'*64,p)
            self.assertEqual(list(Path(t).iterdir()),[])
    def test_size_limit_cleans_up(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'image.iso'
            with self.assertRaises(ValueError):self.transfer(b'excessive','0'*64,p,2)
            self.assertEqual(list(Path(t).iterdir()),[])
    def test_redirect_to_untrusted_domain_rejected(self):
        from smart_os.core.download import OfficialRedirect
        with self.assertRaises(ValueError):OfficialRedirect().redirect_request(None,None,302,'',{},'https://random-driver.example/image.iso')
    def test_official_debian_mirror_server_and_boundary(self):
        validate_url('https://saimei.ftp.acc.umu.se/debian-cd/example.iso')
        with self.assertRaises(ValueError):validate_url('https://ftp.acc.umu.se.evil.example/image.iso')
