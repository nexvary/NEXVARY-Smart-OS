from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import Qt, QObject, Signal, QRunnable, QThreadPool, QSize, QRectF, QSettings
from PySide6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QFont, QFontDatabase, QRawFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QStackedWidget, QTextEdit, QFileDialog, QMessageBox, QFrame, QProgressBar)
from .. import __version__
from ..core.logging import Journal, export_report

TEXT = {
"en": {"linux": "Smart Linux Installer", "driver": "Smart Windows Driver", "tag": "SMART OS SUITE  /  NEXVARY",
 "home": "Overview", "hardware": "Hardware", "iso": "ISO & downloads", "profile": "Install profile", "usb": "USB safety", "logs": "Diagnostics", "devices": "Devices", "backup": "Backup & restore", "updates": "Windows Update",
 "scan": "Scan hardware", "export": "Export report", "back": "Back", "about": "About", "busy": "Working…", "error": "Operation could not complete", "save": "Save", "success": "Operation completed", "alpha": "ALPHA 0.2  ·  Local first",
 "review": "Review before any disk or driver operation.", "select": "Select", "analyze": "Analyze", "details": "Details", "refresh": "Refresh", "notwindows": "Run this application on Windows 10/11 x64 to inspect real Windows devices."},
"ar": {"linux": "مثبّت Linux الذكي", "driver": "تعريفات Windows الذكية", "tag": "SMART OS SUITE  /  NEXVARY",
 "home": "الرئيسية", "hardware": "العتاد", "iso": "ISO والتنزيل", "profile": "ملف التثبيت", "usb": "أمان USB", "logs": "التشخيص", "devices": "الأجهزة", "backup": "نسخ واستعادة", "updates": "تحديثات Windows",
 "scan": "فحص العتاد", "export": "تصدير التقرير", "back": "رجوع", "about": "عن البرنامج", "busy": "جارٍ التنفيذ…", "error": "تعذّر إتمام العملية", "save": "حفظ", "success": "اكتملت العملية", "alpha": "نسخة أولية 0.2 · محلية افتراضيًا",
 "review": "راجع التفاصيل قبل أي عملية على القرص أو التعريفات.", "select": "اختيار", "analyze": "تحليل", "details": "التفاصيل", "refresh": "تحديث", "notwindows": "شغّل البرنامج على Windows 10 أو 11 بمعمارية x64 لفحص أجهزته الحقيقية."}}

STYLE = """
QWidget { background:#090f19; color:#e8edf7; font-size:14px; }
QMainWindow { background:#090f19; }
QLabel#brand {color:#8593ab; font-size:11px; letter-spacing:2px;}
QLabel#title {font-size:26px; font-weight:700;}
QLabel#pageheading {font-size:17px; font-weight:600; color:#d1d9e8; padding:4px 0;}
QLabel#metric {font-size:26px; font-weight:700; background:transparent;}
QLabel#metriclabel {color:#a7b5cd; background:transparent; font-size:12px;}
QProgressBar {border:0; background:#172337;}
QProgressBar::chunk {background:#5f9be7;}
QLabel#subtitle {color:#9daac0; font-size:15px;}
QFrame#card {background:#131d2c; border:1px solid #3e4b60; border-radius:14px;}
QLabel#cardtitle {background:transparent; font-size:20px; font-weight:600;}
QLabel#cardbody {background:transparent; color:#adb9cf; font-size:14px;}
QPushButton {background:#172235; border:1px solid #556277; border-radius:8px; padding:11px 15px; min-height:22px;}
QPushButton:hover {background:#23334c; border-color:#91adcf;}
QPushButton:pressed {background:#304769;}
QPushButton:disabled {color:#758095; background:#151a24;}
QPushButton#primary {background:#225caa; border-color:#6794d3; font-weight:600;}
QPushButton#nav {text-align:left; border:0; background:transparent; padding:10px;}
QPushButton#nav:checked {background:#21334f; border:1px solid #4b658a; color:#c3d9fa;}
QComboBox,QLineEdit,QTextEdit,QPlainTextEdit,QSpinBox {background:#111c2d; border:1px solid #48566c; border-radius:7px; padding:9px; selection-background-color:#325d96;}
QTableWidget {alternate-background-color:#142035; background:#111c2d; border:1px solid #46566e; border-radius:8px; gridline-color:#243249;}
QHeaderView::section {background:#19263a; color:#b3c5df; padding:10px; border:0;}
QScrollBar:vertical {width:9px; background:#101827;}
QScrollBar::handle:vertical {background:#4b5d78; border-radius:4px; min-height:25px;}
QToolTip {background:#223149; color:#f4f6fa; border:1px solid #788cac;}
"""

from .icons import icon, NAV_ICONS
from .panels import ReportPanel, HardwarePanel

class WrappingLabel(QLabel):
    """Reserve actual wrapped height after styling and resizing, across OS fonts."""
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.wordWrap() and self.width()>0:
            needed=self.heightForWidth(self.width())
            if needed>0 and needed!=self.minimumHeight():self.setMinimumHeight(needed)

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
    def __init__(self, kind: str, language=None):
        super().__init__(); self.kind=kind; self.language=language or QSettings("NEXVARY", "SmartOS").value("language", "en"); self.report={}; self.pending=[]
        self.journal=Journal(Path.home()/".smart-os"/f"{kind}.jsonl")
        self.setWindowTitle("NEXVARY " + TEXT["en"][kind]); self.setWindowIcon(icon(kind)); self.resize(1180,760); self.setMinimumSize(1000,700)
        self.pool=QThreadPool(); self.pool.setMaxThreadCount(2)
        self.build()
    def t(self, key): return TEXT[self.language].get(key,key)
    def pair(self,en,ar): return ar if self.language=="ar" else en
    def build(self):
        root=QWidget(); self.setCentralWidget(root); outer=QHBoxLayout(root); outer.setContentsMargins(22,22,22,22); outer.setSpacing(22)
        sidebar=QVBoxLayout(); brand_icon=QLabel(); brand_icon.setPixmap(icon(self.kind,"#82b4f4").pixmap(44,44)); sidebar.addWidget(brand_icon); brand=QLabel("NEXVARY"); brand.setObjectName("cardtitle"); sidebar.addWidget(brand)
        sub=QLabel("SMART OS SUITE"); sub.setObjectName("brand"); sidebar.addWidget(sub); sidebar.addSpacing(12)
        self.nav={}; self.stack=QStackedWidget(); self.stack.setObjectName("pages")
        keys=["home","hardware","iso","profile","usb","logs"] if self.kind=="linux" else ["home","devices","backup","updates","hardware","logs"]
        for i,key in enumerate(keys):
            b=QPushButton(self.t(key).replace("&","&&")); b.setObjectName("nav"); b.setCheckable(True); b.setMinimumWidth(175); b.setIcon(icon(NAV_ICONS[key])); b.setIconSize(QSize(22,22)); b.clicked.connect(lambda _,n=i:self.navigate(n)); sidebar.addWidget(b); self.nav[i]=b
            if self.language=="ar":b.setStyleSheet("text-align:right;")
        sidebar.addStretch(); self.language_selector=QComboBox(); self.language_selector.addItems(["English","العربية"]); self.language_selector.setCurrentIndex(1 if self.language=="ar" else 0); self.language_selector.currentIndexChanged.connect(self.change_language); sidebar.addWidget(self.language_selector)
        b=QPushButton(self.t("about")); b.setIcon(icon("info")); b.clicked.connect(self.about); sidebar.addWidget(b); outer.addLayout(sidebar)
        content=QVBoxLayout(); top=QHBoxLayout(); label=QLabel(self.t("tag")); label.setObjectName("brand"); top.addWidget(label); top.addStretch(); back=QPushButton(self.t("back")); back.setIcon(icon("back")); back.clicked.connect(lambda:self.navigate(0)); top.addWidget(back); content.addLayout(top)
        title=QLabel(self.t(self.kind)); title.setObjectName("title"); content.addWidget(title)
        subtitle=QLabel(self.t("review")); subtitle.setObjectName("subtitle"); content.addWidget(subtitle); content.addSpacing(10); self.page_title=QLabel(); self.page_title.setObjectName("pageheading"); content.addWidget(self.page_title); content.addWidget(self.stack,1)
        self.progress=QProgressBar(); self.progress.setRange(0,0); self.progress.setFixedHeight(3); self.progress.setTextVisible(False); self.progress.hide(); content.addWidget(self.progress)
        self.status=QLabel(self.t("alpha")); self.status.setObjectName("subtitle"); content.addWidget(self.status); outer.addLayout(content,1)
        self.setLayoutDirection(Qt.RightToLeft if self.language=="ar" else Qt.LeftToRight)
        self.keys=keys
    def change_language(self,index):
        saved={key:value.last_data for key,value in self.__dict__.items() if isinstance(value,(ReportPanel,HardwarePanel)) and value.last_data is not None}
        current=self.stack.currentIndex(); self.language="ar" if index else "en"; QSettings("NEXVARY", "SmartOS").setValue("language",self.language); self.build(); self.populate(); self.navigate(current)
        for key,value in saved.items():getattr(self,key).display(value)
    def populate(self): raise NotImplementedError
    def navigate(self,index):
        self.stack.setCurrentIndex(index); self.page_title.setText(self.t(self.keys[index]))
        for i,b in self.nav.items(): b.setChecked(i==index)
    def page(self):
        page=QWidget(); layout=QVBoxLayout(page); layout.setContentsMargins(0,0,0,0); layout.setSpacing(14); self.stack.addWidget(page); return layout
    def card(self,title,body):
        card=QFrame(); card.setObjectName("card"); layout=QVBoxLayout(card); layout.setContentsMargins(20,14,20,14)
        a=WrappingLabel(title); a.setObjectName("cardtitle"); a.setWordWrap(True); layout.addWidget(a)
        b=WrappingLabel(body); b.setObjectName("cardbody"); b.setWordWrap(True); layout.addWidget(b); return card,layout
    def button(self,layout,text,callback,primary=False,symbol=None):
        symbols={"scan_hardware":"chip","scan_devices":"chip","download_dialog":"download","select_iso":"iso","analyze_iso":"search","backup_all":"backup","backup_selected":"backup","preview_restore":"backup","export_machine":"chip","load_profile":"profile","save_profile":"profile","generate_seed":"profile","usb_preview":"usb","search_updates":"updates","analyze_logs":"search","export":"download","export_logs":"download"}
        b=QPushButton(text.replace("&","&&")); b.setIcon(icon(symbol or symbols.get(getattr(callback,"__name__",""), "check" if primary else "logs"))); b.setIconSize(QSize(20,20)); b.clicked.connect(callback)
        if primary:b.setObjectName("primary")
        layout.addWidget(b); return b
    def text_panel(self,layout):
        p=ReportPanel(self.language); layout.addWidget(p,1); return p
    def async_task(self,name,function,done):
        if self.pending:
            QMessageBox.information(self,self.t("busy"),self.pair("Wait for the current operation to finish.","انتظر اكتمال العملية الحالية.")); return
        task=Task(function); self.pending.append(task); self.status.setText(self.t("busy")); self.stack.setEnabled(False); self.language_selector.setEnabled(False); self.progress.show()
        def cleanup():
            self.pending.remove(task); self.stack.setEnabled(True); self.language_selector.setEnabled(True); self.progress.hide(); self.status.setText(self.t("alpha"))
        def success(value):
            cleanup(); self.journal.record(name,"completed"); done(value)
        def failure(message):
            cleanup(); self.journal.record(name,"failed"); QMessageBox.warning(self,self.t("error"),message)
        task.signals.done.connect(success); task.signals.failed.connect(failure); self.pool.start(task)
    def show_json(self,panel,value):panel.display(value)
    def hardware_view(self,layout):
        panel=HardwarePanel(self.language); layout.addWidget(panel,1); return panel
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
    app=QApplication.instance() or QApplication([])
    if not app.property("smartOsFontLoaded"):
        source=Path(__file__).parent/"assets"/"NotoSansArabic.ttf"
        font_id=QFontDatabase.addApplicationFont(str(source))
        families=QFontDatabase.applicationFontFamilies(font_id)
        if not families:raise RuntimeError("Bundled UI font could not load")
        font=QFont(families[0],10); app.setFont(font)
        raw=QRawFont.fromFont(font)
        if any(index==0 for index in raw.glyphIndexesForString("SMART OS العربية 0123456789")):raise RuntimeError("Bundled UI font lacks Arabic or Latin glyphs")
        app.setProperty("smartOsFontLoaded",True)
    app.setStyle("Fusion"); app.setStyleSheet(STYLE); return app
