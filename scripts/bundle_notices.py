"""Keep third-party notices beside the replaceable dynamic libraries."""
from pathlib import Path
import importlib.metadata as metadata
import shutil

root=Path(__file__).resolve().parents[1]
for name in ['SmartLinuxInstaller','SmartWindowsDriver']:
    bundle=root/'dist'/name
    if not bundle.is_dir():continue
    notices=bundle/'THIRD-PARTY-LICENSES';notices.mkdir(exist_ok=True)
    dependencies=['PySide6','PySide6-Essentials','PySide6-Addons','shiboken6','pyinstaller']
    if name=='SmartLinuxInstaller':dependencies+=['pycdlib','PyYAML']
    for package in dependencies:
        distribution=metadata.distribution(package)
        for file in distribution.files or []:
            location=distribution.locate_file(file)
            if location.is_file() and (any(token in str(file).lower() for token in ['license','copying','notice']) or str(file).endswith('/METADATA')):
                target=notices/package/str(file);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(location,target)
    for source in (root/'docs'/'licenses').glob('*.txt'):shutil.copy2(source,notices/source.name)
    shutil.copy2(root/'docs'/'third-party.md',notices/'README.md')
    shutil.copy2(root/'LICENSE',bundle/'LICENSE')
