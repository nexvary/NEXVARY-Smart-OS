# Smart OS 0.2.1 alpha: neon UI and Windows servicing

Build source: `a3c5f3961b3066ef0cc9fe8742a06af7498db03f`, branch `dev/foundation`.
Workflow: https://github.com/nexvary/NEXVARY-Smart-OS/actions/runs/37431450846

## Changes

Both independent Qt applications now use near-black green surfaces, neon green primary actions and navigation selection, colored SVG section icons, distinct application artwork and a compact header/sidebar. Arabic RTL, bundled Arabic/Latin fonts, keyboard focus and language-state preservation remain supported. The ISO page and Windows servicing page are captured along with the dashboards in both languages.

Smart Windows Driver Diagnostics exposes read-only Microsoft DISM CheckHealth, Get-Drivers and WIM/ESD inspection. Raw output preserves line breaks, is escaped before rendering, stays local and is available in the diagnostic report export. These are independently implemented functions, not bundled Dism++ internals. The full Dism++ engine source is unavailable according to its developer; see [servicing scope](windows-servicing.md).

## Local validation

- 64 automated tests passed on Linux.
- 10 UI tests passed at 200% scaling.
- Arabic/English dashboard, ISO and servicing screens inspected visually.
- Platform and administrator guards prevent unsupported DISM execution. WIM/ESD paths remain single argv arguments; invalid types are rejected before execution.

## Remaining work

This is a foundation alpha. Actual driver install/restore/rollback, signature/catalog membership and Windows-native ranking, operation-specific elevation, restore points, online OEM sources and complete offline packs remain incomplete. DISM CheckHealth reads recorded flags rather than performing a full corruption scan. WIM/ESD inspection is implemented but not tested against a real Windows image. Repair, cleanup, registry optimization, image application and driver removal are not offered.

Full Linux deployment, boot-media seed injection, dual-boot resizing, custom ISO builds and Windows USB writing remain incomplete. Physical USB writing and real distro installation are untested. Windows 10/11 physical-device QA is pending; Windows CI uses Server 2022 x64. Executables are not Authenticode-signed.

## Native CI verification

Both jobs concluded success on 2026-10-06: 64 tests per OS, independent native builds, native bundle launch/language checks, Linux X11/Xvfb launch and two Windows Setup install-launch-uninstall checks. Real Windows runner inventory contained 59 devices, 1 missing and 2 needing review. PnPUtil exported 13 OEM INF packages / 56 files; all 56 matched the backup manifest. DISM CheckHealth and Get-Drivers completed successfully. No driver installation or OS deployment was attempted.

Setup archive SHA256 matched the Actions digest: `2f7e0daada4a4ae74be54dd71df4d3465ab3d54716ce424acec43dcef0ab68f2`; ZIP integrity and PE/MZ headers verified.

| Setup | Bytes | SHA256 |
| --- | ---: | --- |
| SmartLinuxInstaller-0.2.1-Setup.exe | 35110774 | `6f6390aff999f1c88047774ceeff8138295c19d8c0dfb0c2c918d2a78244ea0b` |
| SmartWindowsDriver-0.2.1-Setup.exe | 34147594 | `595d98e53ca72030be70cf9b1a1c0224d99837b78cf5746d14bf066cc26dd426` |
