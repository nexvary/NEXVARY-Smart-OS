# Build instructions

Python 3.12 and pip. Install `.[linux,build]` from the repository root. Run `python scripts/build.py` on the target operating system. Outputs are independent onedir bundles. PyInstaller cannot generate Windows EXEs from this Linux environment. The local artifacts in this delivery are Linux x86-64 ELFs.

Windows CI uses windows-2022 and runs the same unit/Qt tests before building. MSI/Setup EXE packaging is not complete until the runner builds and smoke-tests the Windows executables; Inno Setup recipes are provided in `scripts/installers/` for separate per-user setup files. They do not imply a successful installer build. No Authenticode code-signing certificate is available in this delivery.

Keep `_internal` with each executable. Run its `--self-check` switch with `QT_QPA_PLATFORM=offscreen` for an automated GUI boot/language check. Actual GUI testing still needs the platform's display driver, DPI, font and desktop dependencies.
