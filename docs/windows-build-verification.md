# Windows and Linux remote build verification

Build commit: `2880caa6a606dbce53eecf43b39104323cdfaeeb` on `dev/foundation`.
Actions: https://github.com/nexvary/NEXVARY-Smart-OS/actions/runs/37394820275
Both jobs concluded success on 2026-10-06.

- Ubuntu 24.04: 47 tests; two independent native bundles; offscreen boot/language checks; bundled Linux Installer launched through X11/Xvfb successfully.
- Windows Server 2022 x64: 47 tests; two independent native bundles; EXE boot checks; two Inno Setup installers compiled; each installed, launched, and uninstalled successfully.
- Actual Windows PnP inventory: 64 present devices, 1 missing driver, 2 requiring review, 61 with Hardware IDs. These are runner devices, not the user's PC.
- Actual OEM export: 13 INF packages, 56 files, all 56 verified against the backup manifest.
- SmartLinuxInstaller-0.1.0-Setup.exe: 34,682,829 bytes; SHA256 `e1b0bdcacbca325c2841dbab55d24214abfb15cf551443e007ff08a4ae9ba5a5`.
- SmartWindowsDriver-0.1.0-Setup.exe: 33,637,607 bytes; SHA256 `fde90f98ade05a48e9ef0afc759450391159a8cd45eb6171d258d4d3624c2a85`.
- Downloaded Setup artifact archive matched Actions SHA256 `044d5805181e82b36c87d920243d319832d120bf75eafb132c4e883fb53396f0`; archive integrity and both PE/MZ executable headers verified locally.

The Setup tests install the APPLICATIONS, not hardware drivers or Linux itself. Actual driver install/restore/rollback remains blocked; full OS installation, boot-media integration, dual boot, Windows 10/11 physical-device tests and Windows Update driver search are still pending. The first milestone is a foundation prototype, not a complete maintenance suite. Executables are not Authenticode-signed.
