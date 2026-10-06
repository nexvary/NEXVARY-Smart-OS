# Verified 0.2.0 alpha desktop update

Source commit: `9d184c362f3e1b16c9ae029e9680853601b409be`, branch `dev/foundation`.

GitHub Actions: https://github.com/nexvary/NEXVARY-Smart-OS/actions/runs/37423778857

Both ubuntu-24.04 and windows-2022 jobs passed: 59 tests on each OS, both native desktop builds, both native self-checks, and Linux X11/Xvfb launch. On Windows each independent Setup was installed, the installed executable launched/self-checked, and the app uninstalled successfully. This does not test driver installation or operating-system deployment.

Windows Server 2022 x64 runner inventory: 61 devices, 1 missing driver, 2 needing review. PnPUtil exported 13 OEM packages / 56 files, all 56 hash-verified. A real-device offline profile exported and loaded successfully. Read-only UEFI, Fast Startup and BitLocker checks executed; partition readiness remains false pending actual partition/space review.

Windows screenshots were visually reviewed: Arabic and Latin glyphs render correctly with bundled Noto Sans Arabic, meaningful icons are visible, and the device list uses full height until selection. Local offscreen UI tests also passed at QT_SCALE_FACTOR=2. The bundled unmodified font SHA256 is `63111b5b2e074dd48cc67692e0a2726d86ee94c1c37fe8598257b7b4e87e869e`; its OFL license ships with each application.

Downloaded Setup artifact ZIP matched Actions digest `98cf30f3d84e985311c0b12ce81dda58b87f1bf08ab79b4dea0e69d6dbd2c864` and passed ZIP CRC validation.

| Independent Windows installer | Bytes | SHA256 |
| --- | ---: | --- |
| SmartLinuxInstaller-0.2.0-Setup.exe | 35115863 | 7eb0a38a60d9f02a066e54bc9e7a7d16b5f50663edeb19092882e9f0dd5e3891 |
| SmartWindowsDriver-0.2.0-Setup.exe | 34081861 | ec206cb79b43172e2a0eb1fe9161d11486546dd5f91cc4e883138fea41ac3435 |

Limits: no physical Windows 10/11 machine QA, no live Windows Update query test in this release, no physical USB writing, no actual driver install/restore/rollback, no complete Linux installation or partition resizing. EXEs are not Authenticode signed. See phase-02-ui-offline.md for remaining product work; this is not the completed suite or completed original MVP.
