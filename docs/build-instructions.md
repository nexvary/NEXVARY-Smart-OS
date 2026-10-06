# Build instructions

Python 3.12 and pip. Install `.[linux,build]` from the repository root. Run `python scripts/build.py` on the target operating system. Outputs are independent onedir bundles. PyInstaller cannot generate Windows EXEs from this Linux environment. Local scratch builds are Linux x86-64 ELFs; the Windows Setup artifacts now come from the verified Windows Actions runner.

Windows CI uses windows-2022 and runs the same unit/Qt tests before building. Inno Setup recipes in `scripts/installers/` produce two independent per-user Setup EXEs. Actions run 37394820275 compiled both, installed them silently into isolated test directories, boot-checked each installed application and uninstalled each successfully. No Authenticode code-signing certificate is available in this delivery.

Keep `_internal` with each executable. Run its `--self-check` switch with `QT_QPA_PLATFORM=offscreen` for an automated GUI boot/language check. Actual GUI testing still needs the platform's display driver, DPI, font and desktop dependencies.
