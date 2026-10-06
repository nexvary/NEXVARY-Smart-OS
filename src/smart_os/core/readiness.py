"""Read-only preflight. Never changes encryption, registry, boot or partitions."""
import json
import platform
from .process import powershell

SCRIPT=r'''
$mode='unknown'; try {$mode=[string](Get-ComputerInfo -Property BiosFirmwareType -ErrorAction Stop).BiosFirmwareType} catch {}
$fast=$null; try {$fast=(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Power' -ErrorAction Stop).HiberbootEnabled} catch {}
$bitlocker=$null; try {$bitlocker=@(Get-BitLockerVolume -ErrorAction Stop | ForEach-Object {[pscustomobject]@{mount=$_.MountPoint; protection=[string]$_.ProtectionStatus; volume=[string]$_.VolumeStatus; lock=[string]$_.LockStatus}})} catch {}
[pscustomobject]@{boot_mode=$mode; fast_startup=$fast; bitlocker=$bitlocker} | ConvertTo-Json -Depth 4 -Compress
'''

def evaluate(facts):
    checks=[]
    mode=str(facts.get('boot_mode','unknown'))
    checks.append({'check':'boot-mode','state':'passed' if mode.casefold()=='uefi' else 'review', 'value':mode, 'action':'Use installation media matching the current boot mode.'})
    fast=facts.get('fast_startup')
    checks.append({'check':'fast-startup','state':'passed' if fast==0 else 'review' if fast==1 else 'unknown','value':fast,'action':'Disable Fast Startup manually in Windows before accessing Windows volumes from Linux.'})
    volumes=facts.get('bitlocker')
    if not isinstance(volumes,list) or not volumes:
        checks.append({'check':'bitlocker','state':'unknown','value':None,'action':'Check encryption and obtain a recovery key manually. No encryption settings are changed.'})
    else:
        for volume in volumes:
            encrypted=volume.get('volume')!='FullyDecrypted' or volume.get('protection')!='Off' or volume.get('lock')!='Unlocked'
            checks.append({'check':'bitlocker','state':'review' if encrypted else 'passed','value':volume,'action':'Keep a verified recovery key. Review encrypted disks before partition changes; encryption is never disabled automatically.'})
    checks.append({'check':'partition-space','state':'review','value':None,'action':'Verify EFI, recovery partitions and actual unallocated space in the installation disk preview. Filesystem free space is not unallocated space.'})
    return {'checks':checks,'ready_to_partition':False,'automatic_changes':False}

def dual_boot_readiness():
    if platform.system()!='Windows':
        return {'checks':[{'check':'windows-state','state':'unknown','action':'Run this check inside Windows. Linux cannot reliably determine Windows Fast Startup or BitLocker protection.'}], 'ready_to_partition':False,'automatic_changes':False}
    return evaluate(json.loads(powershell(SCRIPT,timeout=120)))
