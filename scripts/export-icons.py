"""Regenerate original application artwork. Development dependency: Pillow."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QPixmap,QPainter,QLinearGradient,QColor,QPen
from smart_os.ui.common import application
from smart_os.ui.icons import svg
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray
from PIL import Image
app=application(); directory=Path('ui/assets'); directory.mkdir(exist_ok=True)
for slug,kind,accent in [('smart-linux-installer','linux','#71b7fa'),('smart-windows-driver','driver','#7ae0c2')]:
    pixmap=QPixmap(512,512);pixmap.fill(Qt.transparent);p=QPainter(pixmap);p.setRenderHint(QPainter.Antialiasing)
    grad=QLinearGradient(0,0,512,512);grad.setColorAt(0,QColor('#1b2b43'));grad.setColorAt(1,QColor('#070c15'))
    p.setBrush(grad);p.setPen(QPen(QColor('#91a3bf'),8));p.drawRoundedRect(QRectF(16,16,480,480),104,104)
    renderer=QSvgRenderer(QByteArray(svg(kind,accent).encode()));renderer.render(p,QRectF(100,83,312,312))
    p.setPen(QPen(QColor(accent),10,Qt.SolidLine,Qt.RoundCap));p.drawLine(198,437,314,437);p.end()
    pixmap.save(str(directory/f'{slug}.png'))
    Image.open(directory/f'{slug}.png').save(directory/f'{slug}.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
