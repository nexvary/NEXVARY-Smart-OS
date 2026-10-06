# SMART OS by NEXVARY

Two independent desktop applications, one local safety core:

- **Smart Linux Installer**: hardware inspection, ISO structure and SHA256 analysis, official HTTPS download, saved profiles, Ubuntu/Debian/Kali preparation seeds, disk/USB safety previews and installer log diagnosis.
- **Smart Windows Driver**: Windows PnP inventory, Hardware/Compatible IDs, Device Manager problem codes, driver inspection, PnPUtil OEM backups, backup integrity checks, local INF matching preview and read-only Windows Update driver search.

**0.1.0-alpha.1 is a preparation and inspection prototype, not a finished installer or driver updater.** Nothing in this release proves successful operating-system installation or Windows driver restoration. Driver installation is deliberately blocked pending native package signature/catalog checks, OS-decorated INF evaluation, a narrow elevation broker, recovery and Windows VM validation.

## Run from source

Python 3.11+ (3.12 recommended), Windows 10/11 x64 or modern Linux desktop.

```sh
python -m pip install ".[linux]"
smart-linux-installer
```

Windows Driver can be installed without the Linux extras:

```powershell
python -m pip install .
smart-windows-driver
```

Each app starts independently. There is no combined EXE. Change English/Arabic in the sidebar. Arabic uses Qt RTL layout; paths, IDs and hashes retain LTR. Diagnostic reports redact device IDs/serials; device details remain visible locally. No telemetry or AI service is contacted.

## Test and build

```sh
python -m pip install ".[linux,build]"
# Linux:
QT_QPA_PLATFORM=offscreen PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/build.py
```

```powershell
# Windows:
$env:QT_QPA_PLATFORM='offscreen'
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python scripts/build.py
```

PyInstaller emits `dist/SmartLinuxInstaller/` and `dist/SmartWindowsDriver/` separately. Build on the target OS. A Linux ELF is never relabeled as a Windows EXE. Keep each executable beside its `_internal` folder. Ubuntu may need `libxcb-cursor0` and normal Qt xcb system libraries for a graphical desktop. Qt offscreen testing does not prove all desktop dependencies are installed.

The repository is `nexvary/NEXVARY-Smart-OS`, branch `dev/foundation`. GitHub Actions run 37394820275 passed on Ubuntu 24.04 and Windows Server 2022: 47 tests per OS, native builds, Qt bundle launch checks, real Windows PnP inventory/OEM export, and separate Setup install-launch-uninstall tests. Windows 10/11 physical devices and driver installation/rollback are still untested. See `docs/windows-build-verification.md`.

## CLI

```sh
smart-os hardware
smart-os iso /path/distribution.iso --sha256 OFFICIAL_SHA256
smart-os seed profile.json /path/distribution.iso --sha256 OFFICIAL_SHA256 --output autoinstall.yaml
smart-os devices
smart-os driver-backup /path/new-backup
smart-os restore-preview /path/backup
smart-os analyze-log /path/installer.log
smart-os usb-preview /dev/sdX /path/distribution.iso --sha256 OFFICIAL_SHA256
```

USB previews include the disk identity, partitions, exact confirmation, image hash and size. Save the JSON plan; a separately invoked **Linux-only** privileged CLI operation can write it:

```sh
smart-os usb-write reviewed-plan.json /path/distribution.iso --confirm 'ERASE /dev/sdX PLAN_HASH_PREFIX'
```

Do not run the entire GUI as root. Raw USB writing is experimental and **not tested on physical USB media** in this delivery. It requires root for that one CLI operation, a serial-identified USB disk, removable flag, no mounts, no protected/unknown/data partitions, exact identity recheck, matching ISO digest, exclusive block-device open and full readback digest. Mounted filesystems must be unmounted manually. These strict checks will intentionally reject many already-formatted USB drives. Windows USB writing is unavailable.

## Current limitations

- ISO distribution detection uses image metadata, not its filename. Unknown/live installers are blocked for seed generation. Ubuntu `install-sources.yaml` is only a Subiquity **candidate**; desktop/server version semantics still need real-image and VM tests.
- Seeds automate locale/keyboard/timezone/packages; storage remains interactive. Ubuntu identity/network remain interactive. They are exported separately, not injected into boot media. No dual-boot shrinking, automated formatting, ISO remastering or OS installation is implemented.
- SHA256 supplied by a user detects corruption only relative to that value. The user must authenticate the official checksum source. Automatic GPG checksum-signature verification is not implemented.
- Hardware scan does not assert firmware support, BitLocker status, Fast Startup, TPM availability or SMART health when they were not actually checked.
- Backup exports third-party OEM drivers only. No Microsoft inbox drivers, OEM software or BIOS are exported. Export may require administrator privileges; narrow automatic elevation is pending.
- INF matching is a **review**, not Windows' authoritative driver ranking. Signature verification, OS build constraints, catalog membership and native ranking are incomplete. Restore/install is blocked; version/date do not override ID matching.
- OEM online connectors, curated offline packs, Network Rescue installation, rollback, restore points, auto repair and checkpoints remain future implementation.

See [verification](docs/verification.md), [architecture](docs/architecture.md), [security](docs/security-model.md), [recovery](docs/recovery-model.md) and [testing](docs/testing-guide.md).
