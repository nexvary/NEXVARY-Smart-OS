# Testing guide

The local gate is unittest plus Qt offscreen GUI smoke tests and native bundle boot checks. Generated ISO files are explicitly fixtures: they test parsing and seed-generation invariants, not boot/install compatibility. Tests never write real disks or alter driver stores.

Safety cases include internal-disk rejection, Windows/EFI/recovery/OEM/data/unknown-partition rejection, changed identities/partitions, missing serial, mounted mapped descendants, wrong confirmation, inadequate size and absent hash. Driver tests cover mismatches, generic versus exact matches, unsigned packages, wrong architecture, version/date non-preference, corrupted manifests, path traversal, injection attempts and truthful non-Windows behavior.

Required integration matrix before a release:

1. Real official installer ISOs for current Debian/Kali/Ubuntu (record version + authenticated digest); boot and seed integration in isolated VMs.
2. Empty VM disk; Windows 10 free space; Windows 11 UEFI with BitLocker; recovery/OEM partitions; EFI target ambiguity; wrong disks.
3. Offline/mirror/DNS/corrupt image/low-space/GRUB failures; verify accurate errors and no unsafe automatic recovery.
4. Windows 10/11 x64 inventory, selected/all OEM exports, backup integrity, Windows Update search failure/success.
5. Native catalog signatures and membership, INF OS build decorations, wrong hardware, test-signing/unsigned packages, OEM generic comparison.
6. Narrow elevation, restore-point failures, installer failures, rollback and actual post-install device state.
7. Physical USB removable classification, mounted disks, hotplug/replacement, partial write/readback mismatch.
8. Real desktop keyboard navigation, 100/150/200% DPI, Arabic text/mixed Hardware IDs and no clipped content.

Remote Windows Actions, VM installs, raw USB media, other distribution downloads and driver installation were not tested in this initial delivery. Never merge these into the count of passing local unit cases.
