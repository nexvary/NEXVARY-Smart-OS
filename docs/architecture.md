# Architecture

`apps/` holds independent entry points. `src/smart_os/core/` contains process boundaries, local reports, hardware/disk inventory, integrity, download allowlist, safety plans and deterministic diagnosis. `installer_engine/` owns ISO inspection, profiles and the experimental Linux USB writer. `distro_adapters/` owns seed formats. `driver_engine/` owns Windows inventory, Driver Store export, backup manifest validation and candidate matching. `ui/` owns common Qt components, background tasks and Arabic/English resources.

The two native executables share source libraries, not a required installed launcher. The driver application's import graph does not require pycdlib or Linux seed generation. The Linux UI has no Windows driver-installing component. `pyproject.toml` exposes Linux analysis dependencies as optional extras.

Read-only UI tasks run in a bounded worker pool. A failed external command cannot become a successful result. One foreground operation is permitted per window; closing while it runs is refused. Process execution never invokes a shell. Windows PowerShell runs fixed scripts encoded as UTF-16LE; variable paths must use literal quoting.

Disk plans are immutable data, including serial, path, size, transport, partition state and ISO hash/length. A SHA256 plan digest binds the exact confirmation. Execution rescans and compares the complete snapshot. Unknown facts must remain unknown, never be upgraded to safe guesses.

Future interfaces: native Windows signature/catalog verifier; scoped privilege broker; distribution capability registry based on inspected ISO/version; native ranking adapter; journaled installation transaction with checkpoint verification; OEM source providers with URL/signature provenance. Add Rescue/Backup/Boot Repair as independent apps reusing these contracts.
