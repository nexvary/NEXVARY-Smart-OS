# Third-party software

The source project is MIT. Dependencies keep their own licenses; this does not relicense Python, PySide6, Qt, pycdlib, PyYAML, PyInstaller or system libraries.

Qt/PySide6 are dynamically bundled, under their applicable LGPL/GPL/commercial terms. The bundle keeps libraries separate in `_internal`, without intentionally restricting modification/replacement or debugging. Included dependency notices and license metadata must ship with redistributed binaries. See Qt/PySide upstream for corresponding source and license obligations:
https://www.qt.io/licensing/open-source-lgpl-obligations
https://doc.qt.io/qtforpython-6/licenses.html
https://code.qt.io/cgit/pyside/pyside-setup.git/

The official Debian ISO used for analysis is not included in application bundles or source delivery. No firmware or driver packages are redistributed in this alpha.

## Bundled UI font
Noto Sans Arabic from https://github.com/google/fonts/tree/main/ofl/notosansarabic, unmodified under SIL Open Font License 1.1. License is bundled beside the font and copied into THIRD-PARTY-LICENSES.
