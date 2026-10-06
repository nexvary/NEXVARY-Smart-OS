> From 0.3.0, the GUI uses a one-operation UAC helper for these DISM tools and OEM backup. See [current elevation and native preflight](windows-preflight.md). The description below records the 0.2.1 starting point.

# Windows servicing and Dism++ scope

The user-provided Dism++ executable was identified statically, not executed or bundled. Dism++ is partially open source; its full engine source is unavailable according to a core developer:
https://github.com/Chuyu-Team/Dism-Multi-language/issues/719

Smart Windows Driver 0.2.1 implements its own read-only adapter using Microsoft's installed DISM, available from Diagnostics:

- CheckHealth reads existing corruption flags. It does not perform a fresh scan or repair.
- Get-Drivers lists third-party drivers in the running Windows installation.
- Get-WimInfo inspects an existing WIM/ESD file without mounting or applying it.

Commands use a fixed allowlist, a fixed System32 executable, argument arrays and no shell. WIM/ESD paths must refer to existing files. Every task records completion/failure in the local activity journal; report export includes real output with the standard diagnostic redaction. Non-Windows hosts and unelevated Windows sessions fail before launching DISM. The application is not configured to always run as administrator; an operation-specific elevation broker is still pending.

This is feature development inspired by the requested maintenance workflow, not a merger or redistribution of Dism++ binaries or engine source. Cleanup, RestoreHealth, registry optimization, image deployment and driver removal are not exposed. They require separate recovery/elevation design and Windows VM validation.

Official command references:
https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/repair-a-windows-image
https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism-image-management-command-line-options-s14

Tests verify platform/permission guards and exact non-destructive command arguments. Windows CI additionally executes CheckHealth and Get-Drivers on the actual runner. WIM/ESD path validation is unit-tested; real image inspection and Windows 10/11 physical-device use remain untested.
