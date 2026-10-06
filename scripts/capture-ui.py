"""Capture real initial screens; does not fabricate hardware data."""
import os,sys,platform
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from smart_os.ui.common import application
from smart_os.linux_app import LinuxWindow
from smart_os.windows_app import DriverWindow
app=application(); output=Path('docs/screenshots'); output.mkdir(exist_ok=True)
for cls in (LinuxWindow,DriverWindow):
    for language in ('en','ar'):
        window=cls(language)
        if '--scan' in sys.argv:
            from smart_os.core.hardware import scan
            if cls is DriverWindow and platform.system()=='Windows':
                from smart_os.driver_engine.inventory import inventory
                window.devices=inventory(); window.render_devices()
            elif cls is LinuxWindow:
                window.inventory=scan(); window.show_json(window.hardware_panel,window.inventory.to_dict()); window.prep_counts[0].setText(window.inventory.architecture)
        window.show(); app.processEvents()
        window.grab().save(str(output/f'{cls.__name__}-{language}.png')); 
        if '--scan' in sys.argv and cls is DriverWindow:
            window.navigate(1); app.processEvents(); window.grab().save(str(output/f'DriverDevices-{language}.png'))
        if cls is DriverWindow:
            if '--scan' in sys.argv and platform.system()=='Windows':
                import json
                verified=json.loads(Path('artifacts/verification/windows-readonly.json').read_text(encoding='utf-8'))
                window.servicing_done(verified['dism']['health'])
            if '--scan' in sys.argv and platform.system()=='Windows' and verified.get('driver_review'):
                window.show_json(window.backup_panel,verified['driver_review']);window.navigate(2);app.processEvents()
                window.grab().save(str(output/f'DriverPreflight-{language}.png'))
            window.navigate(5); app.processEvents(); window.grab().save(str(output/f'WindowsServicing-{language}.png'))
        elif cls is LinuxWindow:
            window.navigate(2); app.processEvents(); window.grab().save(str(output/f'LinuxISO-{language}.png'))
        window.close()
