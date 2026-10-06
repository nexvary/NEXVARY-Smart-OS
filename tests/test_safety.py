from dataclasses import replace
import unittest
from smart_os.core.hardware import Disk, Partition, classify_partition, linux_disks
from smart_os.core.safety import DiskPlan, SafetyError, validate_usb, validate_empty_disk
class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.disk=Disk('/dev/sdz',64*1024**3,'Test USB','stable-serial','usb',True); self.plan=DiskPlan(self.disk,'usb','a'*64,4096)
    def test_identified_blank_usb(self):validate_usb(self.plan,self.disk,self.plan.confirmation)
    def test_never_accept_internal_disks(self):
        for transport,removable in [('nvme',False),('sata',False),('usb',False),('',True)]:
            disk=replace(self.disk,transport=transport,removable=removable); plan=replace(self.plan,target=disk)
            with self.subTest(transport=transport),self.assertRaises(SafetyError):validate_usb(plan,disk,plan.confirmation)
    def test_never_format_protected_partitions(self):
        for kind in ['windows','efi','recovery','oem','unknown','data']:
            disk=replace(self.disk,partitions=(Partition('/dev/sdz1',100,'ntfs',kind),)); plan=replace(self.plan,target=disk)
            with self.subTest(kind=kind),self.assertRaises(SafetyError):validate_usb(plan,disk,plan.confirmation)
    def test_state_change_requires_new_preview(self):
        for disk in [replace(self.disk,serial='different'),replace(self.disk,path='/dev/sdy'),replace(self.disk,size=1),replace(self.disk,readonly=True),replace(self.disk,partitions=(Partition('/dev/sdz1',100,'ext4','linux'),))]:
            with self.assertRaises(SafetyError):validate_usb(self.plan,disk,self.plan.confirmation)
    def test_confirmation_bound_to_plan(self):
        for confirmation in ['', 'yes','ERASE /dev/sdz',self.plan.confirmation+'x']:
            with self.assertRaises(SafetyError):validate_usb(self.plan,self.disk,confirmation)
    def test_missing_serial_blocked(self):
        disk=replace(self.disk,serial=''); plan=replace(self.plan,target=disk)
        with self.assertRaises(SafetyError):validate_usb(plan,disk,plan.confirmation)
    def test_mounted_linux_partition_blocked(self):
        disk=replace(self.disk,partitions=(Partition('/dev/sdz1',100,'ext4','linux',True),)); plan=replace(self.plan,target=disk)
        with self.assertRaises(SafetyError):validate_usb(plan,disk,plan.confirmation)
    def test_size_and_hash_required(self):
        for plan in [replace(self.plan,image_size=0),replace(self.plan,image_size=self.disk.size+1),replace(self.plan,image_sha256='')]:
            with self.assertRaises(SafetyError):validate_usb(plan,self.disk,plan.confirmation)
    def test_whole_disk_filesystem_protected(self):
        disks=linux_disks([{'path':'/dev/sdz','type':'disk','size':10000,'rm':True,'tran':'usb','serial':'x','fstype':'ntfs','mountpoints':['/media/usb']}]); self.assertTrue(disks[0].protected); self.assertTrue(disks[0].mounted)
    def test_mapped_mounted_descendant_blocks_parent(self):
        disks=linux_disks([{'path':'/dev/sdz','type':'disk','size':10000,'children':[{'path':'/dev/sdz1','type':'part','size':9000,'children':[{'type':'crypt','mountpoints':['/']}]}]}]); self.assertTrue(disks[0].mounted)
    def test_windows_efi_recovery_classification(self):
        for fs,typ,expected in [('ntfs','','windows'),('vfat','c12a7328-f81f-11d2-ba4b-00a0c93ec93b','efi'),('','de94bba4-06d1-4d40-a16a-bfd50179d6ac','recovery')]:self.assertEqual(classify_partition(fs,typ,''),expected)
    def test_empty_disk_only(self):
        validate_empty_disk(self.disk)
        with self.assertRaises(SafetyError):validate_empty_disk(replace(self.disk,partitions=(Partition('1',100),)))
