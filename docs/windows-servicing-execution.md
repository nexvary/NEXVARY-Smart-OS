# Windows servicing execution (0.4.0)

Independent Smart Windows Driver now exposes Microsoft's installed DISM:
ScanHealth, AnalyzeComponentStore, confirmed RestoreHealth, and confirmed
StartComponentCleanup. Diagnostics contains all four actions in Arabic and English.
The main app remains unelevated; one fixed operation runs in the existing protected
UAC helper. A negative/cancelled confirmation never starts an operation.

RestoreHealth defaults to the configured Windows repair source / Windows Update.
An optional matching mounted image's Windows folder containing WinSxS is accepted
as one literal argument with LimitAccess. Selecting a WIM/ESD file as a repair
source, mounting images, and applying OS images are not implemented here.

Cleanup first analyzes the store and stops if analysis fails. It does not use
ResetBase, manually delete WinSxS, delete personal files, or alter registry/services.
No cleanup undo is advertised. Output from analyses before/after is displayed;
the app does not invent an amount of recovered space.

Each long operation has a 30 minute DISM timeout. The response pipe stays open
long enough for the entire sequence of analyses/repair/verification. Timeout is
indeterminate because Windows components may already have changed. No automatic
retry, restart or claim of rollback follows it. Exit 3010 means reboot required,
not failure. Successful repair runs ScanHealth afterward unless a reboot is needed.
Health is only verified if DISM explicitly reports no component store corruption.

Testing: unit tests cover confirmation, literal source arguments, return codes,
failure, timeout, cleanup prerequisite, and UI cancellation. The workflow also runs
these commands through the actual UAC helper on its disposable Windows Server 2022
machine and exports native results. CI evidence must be checked before delivery.
This does not establish interactive UAC behavior on a standard user's Windows
10/11 PC, repair of a deliberately corrupted image, or an offline repair source.

Remaining: active driver installation/restore/rollback, full personal-temp cleanup,
reversible optimization policies, Windows image application and a WinPE environment.
No Dism++ executable/code is bundled.

Microsoft references:
- https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/repair-a-windows-image
- https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism-operating-system-package-servicing-command-line-options
