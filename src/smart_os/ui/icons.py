"""Original, resolution-independent NEXVARY interface symbols."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

PATHS = {
 'home': '<path d="m4 14 12-10 12 10M7 12v15h7v-8h4v8h7V12"/>',
 'chip': '<rect x="9" y="9" width="14" height="14" rx="3"/><rect x="13" y="13" width="6" height="6" rx="1"/><path d="M11 4v5m5-5v5m5-5v5M11 23v5m5-5v5m5-5v5M4 11h5m-5 5h5m-5 5h5M23 11h5m-5 5h5m-5 5h5"/>',
 'disk': '<rect x="4" y="7" width="24" height="20" rx="4"/><path d="M4 19h24"/><circle cx="23" cy="23" r="1"/>',
 'iso': '<circle cx="16" cy="16" r="12"/><circle cx="16" cy="16" r="3"/><path d="M9 9a10 10 0 0 1 7-3m7 17a10 10 0 0 1-7 3"/>',
 'shield': '<path d="m16 3 11 5v9c0 6-7 11-11 13C12 28 5 23 5 17V8Z"/><path d="m11 16 4 4 7-8"/>',
 'download': '<path d="M16 3v18m-7-7 7 7 7-7M5 23v5h22v-5"/>',
 'backup': '<path d="M5 11h22v17H5ZM3 4h26v7H3Zm9 13h8m-4 0v7"/>',
 'usb': '<path d="M16 28V5m-4 4 4-5 4 5M16 21l-7-5v-5m7 7 7-4V9"/><circle cx="9" cy="9" r="2"/><rect x="21" y="5" width="4" height="4"/><circle cx="16" cy="27" r="2"/>',
 'logs': '<path d="M8 3h11l6 6v20H8ZM19 3v7h6M12 15h9m-9 5h9m-9 5h5"/>',
 'profile': '<path d="M5 8h22M5 16h22M5 24h22"/><circle cx="12" cy="8" r="3" fill="{bg}"/><circle cx="22" cy="16" r="3" fill="{bg}"/><circle cx="10" cy="24" r="3" fill="{bg}"/>',
 'updates': '<path d="M26 12A11 11 0 0 0 7 7L3 11m0-7v7h7m-4 9a11 11 0 0 0 19 5l4-4m0 7v-7h-7"/>',
 'network': '<path d="M3 11a20 20 0 0 1 26 0M7 16a14 14 0 0 1 18 0m-13 5a7 7 0 0 1 8 0"/><circle cx="16" cy="27" r="1"/>',
 'search': '<circle cx="14" cy="14" r="9"/><path d="m21 21 8 8"/>',
 'back': '<path d="m17 6-10 10 10 10M7 16h22"/>',
 'info': '<circle cx="16" cy="16" r="12"/><path d="M16 14v9m0-14v1"/>',
 'check': '<path d="m5 16 7 7L27 8"/>',
 'warning': '<path d="m16 4 13 24H3ZM16 12v7m0 4v1"/>',
 'linux': '<path d="M5 6h22v18H5ZM10 11l4 4-4 4m7 0h5M11 29h10m-5-5v5"/>',
 'driver': '<rect x="4" y="4" width="24" height="17" rx="3"/><path d="M16 21v7m-6 0h12M9 10h6m-6 5h10m3-5h1"/>',
}
NAV_ICONS = {'hardware':'chip', 'devices':'chip', 'logs':'logs', 'home':'home', 'iso':'iso', 'profile':'profile', 'usb':'usb', 'backup':'backup', 'updates':'updates'}

def svg(kind, color='#b6c5db'):
    body=PATHS.get(kind, PATHS['logs']).replace('{bg}', '#101b2b')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><g fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'

def icon(kind, color='#b6c5db'):
    renderer=QSvgRenderer(QByteArray(svg(kind,color).encode())); result=QIcon()
    for size in (24,32,48,64,128,256):
        pixmap=QPixmap(size,size); pixmap.fill(Qt.transparent)
        painter=QPainter(pixmap); renderer.render(painter); painter.end(); result.addPixmap(pixmap)
    return result
