# Foundation verification — 0.1.0-alpha.1

Date: 2026-10-06 (Cairo). Branch: `dev/foundation`. Local commit is recorded in the delivery report and source archive git bundle.

## Verified locally

- 47 unittest cases passed, including Qt offscreen UI checks.
- Both independent PyInstaller Linux x86-64 builds passed.
- Both bundled executables passed `--self-check`: six reachable screens and English/Arabic RTL.
- Actual environment hardware scan returned Linux x86_64, an AMD EPYC CPU, RAM, two exposed disks and eight PCI/USB records. This container inventory is not the user's laptop inventory.
- Downloaded the official Debian 13.7.0 amd64 netinst ISO (792,723,456 bytes), verified it against the SHA256SUMS value fetched over official HTTPS, inspected its real structure and generated a separate Preseed seed. Detected Debian Installer, amd64, UEFI and Legacy. This did not boot or install Debian. Checksum-file GPG signatures were not verified.
- Local INF matching, protected-partition rejection, changed-disk rejection, ISO fixture detection/checksum failure, profile validation, corruption/path traversal and report redaction passed.
- English and Arabic screenshots captured from the real Qt applications, not design mockups.
- Windows Driver bundle import analysis contains no Linux ISO analyzer, pycdlib or distro adapter.

## Build limitation

PyInstaller warned that `libxcb-cursor.so.0` is absent in the current runtime. GUI checks used Qt offscreen. A package-install attempt failed because the runtime could not switch package-manager identities; package indexes were unavailable to the read-only download fallback. Standard desktop/X11 validation was not completed locally; the later Ubuntu Actions build passed the bundled-app launch check via Xvfb after installing the full Qt X11 dependencies. Install normal Qt xcb libraries, including libxcb-cursor0, on the target Linux desktop.

## Not verified or not implemented

- The source is now on GitHub. Remote build/integration results are recorded in `windows-build-verification.md`; the initial missing-repository blocker was resolved.
- Windows native builds, PnP inventory, OEM export and Setup tests passed on Windows Server 2022. Windows 10/11 physical hardware, Windows Update queries and code signing remain untested/unavailable.
- Full VM Linux boot/install, dual boot, partition shrinking/formatting, GRUB/EFI repair: not implemented or tested.
- Raw USB write/readback: implementation present, no physical-device testing; Windows writer unavailable.
- Native driver signature/catalog membership, OS decorations, safe installation/restore, restore points, rollback and OEM download integrations: pending; installation remains blocked.
- Firmware compatibility, BitLocker/Fast Startup/TPM/SMART verification: not reported as established.
- Automated signed checksum verification, complete unattended ISO building, checkpoints and auto repair: pending.

Do not describe this release as a finished OS installer, driver updater, or completed MVP. It is the first verified foundation prototype.
