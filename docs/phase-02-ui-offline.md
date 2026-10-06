# Smart OS 0.2.0 alpha: interface and read-only tools

Two applications remain independent. This release improves the actual Qt desktop applications, not an HTML mockup.

- Original SVG interface icons render at multiple resolutions. Linux preparation and Windows drivers have distinct application and Setup icons.
- Dark navy surfaces, silver borders, readable report tables, hardware disk table, state colors and honest unscanned dashboard counts.
- Arabic RTL and English; selected language persists. Profile fields, ISO selection, report results, device filters and selected device survive language changes.
- Device search uses names, manufacturer and Hardware/Compatible IDs. Missing, review and network filters use the real inventory. Network rescue is an inspection filter; it does not yet download or install drivers.
- Machine profile export is explicit and local, includes Hardware/Compatible IDs for portable matching, and omits instance IDs and serial numbers. Another computer can load this x64 profile and match a verified local driver backup. No online retrieval is implemented.
- Read-only Windows preflight checks boot mode, Fast Startup and BitLocker. Missing permissions or unavailable data remain unknown. Encryption is never disabled. Space/EFI review remains required, so this check never authorizes partitioning.

## Verification

Run `QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v` on Linux. Windows runners set the same environment in the workflow. Tests cover profile corruption, architecture rejection, no overwrite, encrypted and unknown states, filter accuracy, report HTML escaping, language state preservation and minimum-window text fit in both languages, alongside previous disk/driver/ISO safety tests.

`python scripts/capture-ui.py` captures real, initially unscanned UI. `--scan` uses the current machine's real inventory; no sample devices are fabricated. CI uploads screenshot artifacts per OS. `python scripts/export-icons.py` reproduces application PNG/ICO assets (development dependency Pillow).

## Remaining product work

This is an alpha foundation, not the complete MVP or product. Actual driver installation/restore, catalog membership and OS compatibility verification, privilege helper, restore-point/rollback validation, signed distribution and Windows 10/11 physical-machine QA are pending. Complete Linux unattended deployment, partition resizing, bootable environment, custom ISO injection, Windows USB writing and automatic repair are also pending. No button claims those operations have succeeded.

Official references for read-only checks:
- https://learn.microsoft.com/en-us/powershell/module/bitlocker/get-bitlockervolume
- https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/get-computerinfo
