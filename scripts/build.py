"""Build two independent native desktop bundles, on the target OS."""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
for slug,name in [("smart-linux-installer","SmartLinuxInstaller"),("smart-windows-driver","SmartWindowsDriver")]:
    subprocess.run([sys.executable,"-m","PyInstaller","--noconfirm","--clean","--windowed","--onedir",
      "--add-data",str(root/"src/smart_os/ui/assets")+":smart_os/ui/assets","--name",name,"--icon",str(root/f"ui/assets/{slug}.ico"),"--paths",str(root/"src"),"--exclude-module","PySide6.QtWebEngineWidgets",
      "--exclude-module","PySide6.QtWebEngineCore","--exclude-module","PySide6.QtQml",
      str(root/"apps"/slug/"main.py")],cwd=root,check=True)

subprocess.run([sys.executable,str(root/"scripts/bundle_notices.py")],cwd=root,check=True)

if sys.platform=='win32':
    import shutil
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--name','SmartOSPrivilegeHelper','--paths',str(root/'src'),'--exclude-module','PySide6',str(root/'apps/privilege-helper/main.py')],cwd=root,check=True)
    shutil.move(str(root/'dist/SmartOSPrivilegeHelper'),str(root/'dist/SmartWindowsDriver/_privilege'))
