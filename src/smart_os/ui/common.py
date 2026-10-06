from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool, QSize, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QStackedWidget, QTextEdit, QFileDialog, QMessageBox, QFrame)
from .. import __version__
from ..core.logging import Journal, export_report

TEXT = {
"en": {"linux": "Smart Linux Installer", "driver": "Smart Windows Driver", "tag": "SMART OS SUITE  /  NEXVARY",
 "home": "Overview", "hardware": "Hardware", "iso": "ISO & downloads", "profile": "Install profile", "usb": "USB safety", "logs": "Diagnostics", "devices": "Devices", "backup": "Backup & restore", "updates": "Windows Update",
 "scan": "Scan hardware", "export": "Export report", "back": "Back", "about": "About", "busy": "Working…", "error": "Operation could not complete", "save": "Save", "success": "Operation completed", "alpha": "ALPHA 0.1  ·  Local first",
 "review": "Review before any disk or driver operation.", "select": "Select", "analyze": "Analyze", "details": "Details", "refresh": "Refresh", "notwindows": "Run this application on Windows 10/11 x64 to inspect real Windows devices."},
"ar": {"linux": "مثبّت Linux الذكي", "driver": "تعريفات Windows الذكية", "tag": "SMART OS SUITE  /  NEXVARY",
 "home": "الرئيسية", "hardware": "العتاد", "iso": "ISO والتنزيل", "profile": "ملف التثبيت", "usb": "أمان USB", "logs": "التشخيص", "devices": "الأجهزة", "backup": "نسخ واستعادة", "updates": "تحديثات Windows",
 "scan": "فحص العتاد", "export": "تصدير التقرير", "back": "رجوع", "about": "عن البرنامج", "busy": "جارٍ التنفيذ…", "error": "تعذّر إتمام العملية", "save": "حفظ", "success": "اكتملت العملية", "alpha": "نسخة أولية 0.1 · محلية افتراضيًا",
 "review": "راجع التفاصيل قبل أي عملية على القرص أو التعريفات.", "select": "اختيار", "analyze": "تحليل", "details": "التفاصيل", "refresh": "تحديث", "notwindows": "شغّل البرنامج على Windows 10 أو 11 بمعمارية x64 لفحص أجهزته الحقيقية."}}

STYLE = """
QWidget { background:#0b101a; color:#e8edf7; font-size:14px; }
QMainWindow { background:#0b101a; }
QLabel#brand {color:#8593ab; font-size:11px; letter-spacing:2px;}
QLabel#title {font-size:30px; font-weight:700;}
QLabel#subtitle {color:#9daac0; font-size:15px;}
QFrame#card {background:#131d2c; border:1px solid #49566a; border-radius:14px;}
QLabel#cardtitle {background:transparent; font-size:20px; font-weight:600;}
QLabel#cardbody {background:transparent; color:#adb9cf; font-size:14px;}
QPushButton {background:#172235; border:1px solid #556277; border-radius:8px; padding:11px 15px; min-height:22px;}
QPushButton:hover {background:#23334c; border-color:#91adcf;}
QPushButton:pressed {background:#304769;}
QPushButton:disabled {color:#758095; background:#151a24;}
QPushButton#primary {background:#2963b8; border-color:#6794d3; font-weight:600;}
QPushButton#nav {text-align:left; border:0; background:transparent; padding:12px;}
QPushButton#nav:checked {background:#21334f; border:1px solid #4b658a; color:#c3d9fa;}
QComboBox,QLineEdit,QTextEdit,QPlainTextEdit,QSpinBox {background:#111c2d; border:1px solid #48566c; border-radius:7px; padding:9px; selection-background-color:#325d96;}
QTableWidget {background:#111c2d; border:1px solid #46566e; border-radius:8px; gridline-color:#243249;}
QHeaderView::section {background:#19263a; color:#b3c5df; padding:10px; border:0;}
QScrollBar:vertical {width:9px; background:#101827;}
QScrollBar::handle:vertical {background:#4b5d78; border-radius:4px; min-height:25px;}
QToolTip {background:#223149; color:#f4f6fa; border:1px solid #788cac;}
"""

def icon(kind: str, color="#a9c5e9"):
    pixmap = QPixmap(32, 32); pixmap.fill(Qt.transparent)
    p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(color), 2.2)); p.setBrush(Qt.NoBrush)
    if kind == "disk":
        p.drawRoundedRect(QRectF(5, 7, 22, 19), 4, 4); p.drawLine(6, 19, 26, 19); p.drawEllipse(21, 22, 2, 2)
    elif kind == "chip":
        p.drawRoundedRect(QRectF(9, 9, 14, 14), 2, 2)
        for n in [11, 16, 21]:
            p.drawLine(n, 4, n, 8); p.drawLine(n, 24, n, 28); p.drawLine(4, n, 8, n); p.drawLine(24, n, 28, n)
    elif kind == "shield":
        from PySide6.QtGui import QPainterPath
        path=QPainterPath(); path.moveTo(16,4); path.lineTo(27,9); path.lineTo(25,21); path.quadTo(21,27,16,29); path.quadTo(10,25,7,21); path.lineTo(5,9); path.closeSubpath(); p.drawPath(path)
        p.drawLine(11,16,15,20); p.drawLine(15,20,22,12)
    elif kind == "download":
        p.drawLine(16,4,16,21); p.drawLine(9,14,16,21); p.drawLine(23,14,16,21); p.drawLine(5,24,5,28); p.drawLine(5,28,27,28); p.drawLine(27,28,27,24)
    else:
        p.drawRoundedRect(QRectF(7, 4, 18, 24), 3, 3)
        for y in [11,16,21]: p.drawLine(11,y,21,y)
    p.end(); return QIcon(pixmap)

class Signals(QObject):
    done = Signal(object)
    failed = Signal(str)
class Task(QRunnable):
    def __init__(self, function):
        super().__init__(); self.function=function; self.signals=Signals()
    def run(self):
        try: self.signals.done.emit(self.function())
        except Exception as exc: self.signals.failed.emit(str(exc))

class BaseWindow(QMainWindow):
    def __init__(self, kind: str, language="en"):
        super().__init__(); self.kind=kind; self.language=language; self.report={}; self.pending=[]
        self.journal=Journal(Path.home()/".smart-os"/f"{kind}.jsonl")
        self.setWindowTitle("NEXVARY " + TEXT["en"][kind]); self.setWindowIcon(icon("shield")); self.resize(1180,760); self.setMinimumSize(900,620)
        self.pool=QThreadPool(); self.pool.setMaxThreadCount(2)
        self.build()
    def t(self, key): return TEXT[self.language].get(key,key)
    def pair(self,en,ar): return ar if self.language=="ar" else en
    def build(self):
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(22,22,22,22); outer.setSpacing(22)
        sidebar=QVBoxLayout(); brand=QLabel("NEXVARY"); brand.setObjectName("cardtitle"); sidebar.addWidget(brand)
        sub=QLabel("SMART OS SUITE"); sub.setObjectName("brand"); sidebar.addWidget(sub); sidebar.addSpacing(22)
        self.nav={}; self.stack=QStackedWidget()
        keys=["home","hardware","iso","profile","usb","logs"] if self.kind=="linux" else ["home","devices","backup","updates","hardware","logs"]
        for i,key in enumerate(keys):
            b=QPushButton(self.t(key).replace("&","&&")); b.setObjectName("nav"); b.setCheckable(True); b.setMinimumWidth(175); b.setIcon(icon("chip" if key in {"devices","hardware"} else "disk" if key in {"usb","iso"} else "doc")); b.setIconSize(QSize(22,22)); b.clicked.connect(lambda _,n=i:self.navigate(n)); sidebar.addWidget(b); self.nav[i]=b
            if self.language=="ar":b.setStyleSheet("text-align:right;")
        sidebar.addStretch(); self.language_selector=QComboBox(); self.language_selector.addItems(["English","العربية"]); self.language_selector.setCurrentIndex(1 if self.language=="ar" else 0); self.language_selector.currentIndexChanged.connect(self.change_language); sidebar.addWidget(self.language_selector)
        b=QPushButton(self.t("about")); b.clicked.connect(self.about); sidebar.addWidget(b); outer.addLayout(sidebar)
        content=QVBoxLayout(); top=QHBoxLayout(); label=QLabel(self.t("tag")); label.setObjectName("brand"); top.addWidget(label); top.addStretch(); back=QPushButton(self.t("back")); back.clicked.connect(lambda:self.navigate(0)); top.addWidget(back); content.addLayout(top)
        title=QLabel(self.t(self.kind)); title.setObjectName("title"); content.addWidget(title)
        subtitle=QLabel(self.t("review")); subtitle.setObjectName("subtitle"); content.addWidget(subtitle); content.addSpacing(14); content.addWidget(self.stack,1)
        self.status=QLabel(self.t("alpha")); self.status.setObjectName("subtitle"); content.addWidget(self.status); outer.addLayout(content,1)
        self.setLayoutDirection(Qt.RightToLeft if self.language=="ar" else Qt.LeftToRight)
        self.keys=keys
    def change_language(self,index):
        self.language="ar" if index else "en"; self.build(); self.populate(); self.navigate(0)
    def populate(self): raise NotImplementedError
    def navigate(self,index):
        self.stack.setCurrentIndex(index)
        for i,b in self.nav.items(): b.setChecked(i==index)
    def page(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(14); self.stack.addWidget(page); return layout
    def card(self,title,body):
        card=QFrame(); card.setObjectName("card"); layout=QVBoxLayout(card); layout.setContentsMargins(20,18,20,18)
        a=QLabel(title); a.setObjectName("cardtitle"); a.setWordWrap(True); layout.addWidget(a)
        b=QLabel(body); b.setObjectName("cardbody"); b.setWordWrap(True); layout.addWidget(b); return card,layout
    def button(self,layout,text,callback,primary=False):
        b=QPushButton(text.replace("&","&&")); b.setIcon(icon("shield" if primary else "doc")); b.setIconSize(QSize(20,20)); b.clicked.connect(callback)
        if primary:b.setObjectName("primary")
        layout.addWidget(b); return b
    def text_panel(self,layout):
        p=QTextEdit(); p.setReadOnly(True); p.setLayoutDirection(Qt.LeftToRight); p.setFont(QFont("Consolas",11)); layout.addWidget(p,1); return p
    def async_task(self,name,function,done):
        if self.pending:
            QMessageBox.information(self,self.t("busy"),self.pair("Wait for the current operation to finish.","انتظر اكتمال العملية الحالية.")); return
        task=Task(function); self.pending.append(task); self.status.setText(self.t("busy")); self.centralWidget().setEnabled(False)
        def cleanup():
            self.pending.remove(task); self.centralWidget().setEnabled(True); self.status.setText(self.t("alpha"))
        def success(value):
            cleanup(); self.journal.record(name,"completed"); done(value)
        def failure(message):
            cleanup(); self.journal.record(name,"failed"); QMessageBox.warning(self,self.t("error"),message)
        task.signals.done.connect(success); task.signals.failed.connect(failure); self.pool.start(task)
    def show_json(self,panel,value):panel.setPlainText(json.dumps(value,indent=2,ensure_ascii=False))
    def export(self):
        if not self.report: QMessageBox.information(self,self.t("export"),self.pair("Scan first.","نفّذ الفحص أولًا.")); return
        path,_=QFileDialog.getSaveFileName(self,self.t("export"),"smart-os-report.json","JSON (*.json)")
        if path: export_report(Path(path),self.report)
    def about(self):
        QMessageBox.information(self,self.t("about"),f"SMART OS by NEXVARY\n{__version__}\nhttps://nexvary.com\n"+self.pair("Independent apps. Local reports. No telemetry.\nAlpha: see release verification for untested operations.","تطبيقان مستقلان. تقارير محلية دون إرسال تلقائي.\nنسخة أولية: راجع تقرير الاختبار لمعرفة الحدود الحالية."))
    def closeEvent(self,event):
        if self.pending:
            QMessageBox.information(self,self.t("busy"),self.pair("Wait until the operation completes before closing.","انتظر اكتمال العملية قبل إغلاق البرنامج.")); event.ignore()
        else:event.accept()

def application():
    app=QApplication.instance() or QApplication([]); app.setStyle("Fusion"); app.setStyleSheet(STYLE); return app
