# Windows driver preflight and narrow elevation (0.3.0 alpha)

Smart Windows Driver now offers **Devices → Review local INF**. Select a real device, choose a local package INF, and review the result on Backup & restore. No driver install command is run.

1. Match hardware IDs conservatively. Compatible IDs alone require OEM review.
2. SetupVerifyInfFileW verifies the INF signature for the running platform.
3. WinVerifyTrust verifies each payload against the explicit signed catalog using SIP-aware SHA256/SHA1 hashes. Cached revocation policy fails closed on unknown trust. No WHQL certification is inferred.
4. SetupAPI enumerates the compatible driver list for the selected local device and the single INF. Windows resolves current OS/model decorations and supplies its native driver rank (lower is better). Native audits run in short-lived unprivileged processes so provider catalog caches release their file handles before returning. Package fingerprints are checked again after verification to detect concurrent edits.
5. Firmware, system, storage and security classes stay blocked. A review digest binds device identity, current driver and package files. Passing preflight does not authorize installation.

Extra/unlisted payload files, untrusted catalogs, unsupported INF parsing or unavailable Windows APIs can intentionally reject a package. An incomplete offline trust cache may also block verification. Native trust is inspected on the current OS, not predicted for an exported profile from another computer.

## Privilege helper

The GUI remains unelevated. Backups and DISM inspection request a separate helper through ShellExecuteEx `runas`. One helper performs one request, then exits. A local message pipe has an explicit owner/admin/System ACL, rejects remote clients, limits sizes and binds nonce, process IDs and request digest. No elevated response files or shell/script paths are accepted.

Allowed operations are CheckHealth, Get-Drivers, WIM/ESD inspection and export of a validated OEM INF (or all OEM drivers) into a new backup folder. There are no install, remove, reboot, registry or general-shell operations in the protocol. Fixed Windows executables resolve through GetSystemDirectoryW, and system DLL loading uses System32-only search. User cancellation returns without executing the operation.

The Windows bundle includes `_privilege/SmartOSPrivilegeHelper.exe` and its own Python runtime. This is an internal component of Smart Windows Driver; the Linux preparation application remains independent.

## Validation and remaining gate

Unit tests cover unmatched, untrusted, native OS mismatch, generic-only matches, sensitive classes, plan digest changes and malformed/unsafe privilege requests. Windows CI exercises the actual helper RPC with an already elevated runner token, native signature/catalog membership on real OEM exports, compatible-driver enumeration and rejection of a modified payload copy. Native and installed-bundle helper checks are part of the Windows build.

The interactive UAC consent/cancellation desktop flow and standard-user/different-admin-account cases still need Windows 10/11 VM testing. Active installation/restore, restore points and rollback are not yet enabled; they require a separate VM recovery test. No source-only or CI result is presented as a successful driver installation.

Microsoft references:
- https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupverifyinffilew
- https://learn.microsoft.com/en-us/windows/win32/api/wintrust/ns-wintrust-wintrust_catalog_info
- https://learn.microsoft.com/en-us/windows/win32/api/mscat/nf-mscat-cryptcatadmincalchashfromfilehandle2
- https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-shellexecuteinfow
- https://learn.microsoft.com/en-us/windows/win32/ipc/named-pipe-security-and-access-rights
