# Verified Smart OS 0.3.0 alpha milestone

Build source: `7416961c91fcbf8c36ec08f7b29603532bb79c6a` on `dev/foundation`.
Workflow: https://github.com/nexvary/NEXVARY-Smart-OS/actions/runs/37511580427
Both Ubuntu 24.04 and Windows Server 2022 x64 concluded success on 2026-10-06.

See [native preflight and elevation architecture](windows-preflight.md).

- 79 tests per OS; 10 local UI tests at 200% scale.
- Independent native application builds and launch/language checks; Linux X11/Xvfb launch.
- Two Windows Setup files installed, launched and uninstalled. Both installed and unpackaged applications passed the privilege-helper and unsigned-audit checks.
- Real runner inventory: 59 devices. Helper RPC exported 13 OEM packages / 56 files; manifest verification passed.
- All 13 exported OEM packages passed native INF/catalog/payload trust checks. One package had a Windows-compatible installed device; Mellanox ConnectX-4 Lx passed the complete exact-ID/native/trust/snapshot review.
- Modifying executable bytes in a copied package was rejected.
- Original native catalog cache lock during cleanup was fixed with short-lived audit processes; final tests pass without suppressing cleanup errors.
- Setup ZIP SHA256 matched Actions `sha256:b542c21a65c2eb7c384b50390aa5927f1b9f9b041cb368293e1051085a8b8044`; ZIP and PE/MZ headers checked.

| Setup | Bytes | SHA256 |
| --- | ---: | --- |
| SmartLinuxInstaller-0.3.0-Setup.exe | 35116218 | `bdb1045a0b7496cad02eecd0637d60ebf86384208a6e5f04bbcdb7005aa41a4e` |
| SmartWindowsDriver-0.3.0-Setup.exe | 40356346 | `36d00539e95aa94c5656cd6a4f312ac59e554f1024cee4fafb71b4a9cce9ece8` |

Active driver mutation, restore points/rollback, standard-user interactive UAC and Windows 10/11 physical-device tests remain untested/incomplete. CheckHealth/Get-Drivers and backup RPC were exercised with an already elevated runner token; no consent dialog was tested. WIM/ESD inspection and WUA search lack real-source tests. Full Linux deployment, boot-media integration, partition resizing and Windows USB writing remain incomplete. Executables are not Authenticode-signed. This is a foundation alpha, not the finished MVP or product.
