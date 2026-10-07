# Verified 0.4.0 Windows servicing milestone

Build source: `b6cd283bd3954dc440a9dbaa3e4d2cce151bf400`, branch `dev/foundation`.
[Actions 37582039447](https://github.com/nexvary/NEXVARY-Smart-OS/actions/runs/37582039447)
passed on Ubuntu 24.04 and Windows Server 2022 x64, 89 tests each.
Both native bundles and the two independent Windows Setup files built. Setup
install, launch, packaged/installed helper checks, native audits and uninstall passed.

Real fixed-operation helper commands on the disposable Windows runner:

| Operation | Exit | Result |
| --- | --- | --- |
| ScanHealth | 0 | Completed |
| AnalyzeComponentStore | 0 | Completed |
| RestoreHealth | 0 | Completed; subsequent ScanHealth confirmed healthy |
| StartComponentCleanup | 0 | Completed; analyses before and after, no ResetBase |

No restart was required or initiated. The first run passed these actual operations
but failed to export its report because of reversed arguments. The export was fixed,
covered by a regression test, and native operations and the complete workflow reran.
Do not treat the first failed workflow as a completed release gate.

The Windows hardware run found 59 devices, one missing driver and two needing
review. PnPUtil exported 13 OEM packages / 56 files, all manifest hashes verified.
All 13 passed native catalog/payload trust, one package was compatible through
SetupAPI, and modified payload bytes were rejected. No active driver was installed.
Local Arabic/English servicing controls fit 1000x700; UI tests also passed at 200% DPI.

Remaining untested: interactive UAC from a standard user, physical Windows 10/11,
a deliberately corrupted image, a local mounted repair source and actual reboot-
required conditions. Driver installation/restore/rollback, full temporary-file
cleanup, optimization policies, Windows image application/WinPE and full Linux
deployment remain incomplete. Setup files are not Authenticode-signed.

- SmartWindowsDriver-0.4.0-Setup.exe: 40,367,339 bytes, SHA256
  `9abd7bc58da8e186428dca3a99d73d568436e439fa88454efbbdeaa59c0f4c6a`.
- SmartLinuxInstaller-0.4.0-Setup.exe: 35,119,592 bytes, SHA256
  `9fa35a26d9782951fc0e887e5f6cfb3c081815e2f71e4c5d2a215e26a87ace6b`.

Detailed behavior: [Windows servicing execution](windows-servicing-execution.md).
No Dism++ binary or source code is redistributed.
