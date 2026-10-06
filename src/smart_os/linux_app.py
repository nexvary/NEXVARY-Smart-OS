from __future__ import annotations
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QFormLayout, QMessageBox, QWidget, QInputDialog, QDialog, QVBoxLayout)
from .ui.common import BaseWindow, application
from .ui.panels import metrics
from .core.hardware import scan
from .core.readiness import dual_boot_readiness
from .core.safety import DiskPlan
from .core.download import CATALOG, download_iso
from .core.diagnostics import analyze_log
from .installer_engine.iso import analyze
from .installer_engine.profiles import InstallationProfile, PACKAGES
from .distro_adapters.config import generate

class LinuxWindow(BaseWindow):
    def __init__(self,language=None):
        self.inventory=None; self.iso_report=None; self.preparation_state={}
        super().__init__("linux",language); self.populate(); self.navigate(0)
    def populate(self):
        p=self.page()
        card,c=self.card(self.pair("Prepare with confidence","جهّز نظامك بثقة"),self.pair("Inspect your hardware, verify an ISO and create a reusable installation profile. Storage and passwords remain interactive in this alpha.","افحص العتاد وتحقق من ISO وجهّز ملف تثبيت قابلًا لإعادة الاستخدام. اختيار الأقسام وكلمة المرور تفاعليان في هذه النسخة.")); p.addWidget(card)
        self.prep_counts=metrics(p,[(self.pair("Hardware","العتاد"),self.pair("Not scanned","لم يُفحص") if self.inventory is None else self.inventory.architecture,"#5bc9ff"),(self.pair("ISO verification","التحقق من ISO"),self.pair("Not checked","لم يُفحص") if self.iso_report is None else self.iso_report.distribution,"#86ff4a"),(self.pair("Supported adapters","محوّلات مدعومة"),"3","#c5e4d0")])
        for widget in self.prep_counts:widget.setStyleSheet(widget.styleSheet()+";font-size:17px;")
        row=QHBoxLayout(); self.button(row,self.t("scan"),self.scan_hardware,True); self.button(row,self.t("iso"),lambda:self.navigate(2)); p.addLayout(row)
        card,c=self.card(self.pair("Three distribution adapters","ثلاثة محوّلات للتوزيعات"),self.pair("Ubuntu uses Subiquity; Debian and Kali use Debian Installer. Live images require a separate compatibility review.","Ubuntu عبر صور Subiquity المناسبة. Debian وKali عبر صور Debian Installer. صور Live تُفحص دون افتراض دعم التثبيت الآلي.")); p.addWidget(card)
        note=QLabel(self.pair("Your original ISO stays intact. Disk formatting is not performed by this desktop app.","يبقى ملف ISO الأصلي كما هو. تطبيق سطح المكتب لا ينفّذ تهيئة الأقراص.")); note.setObjectName("subtitle"); note.setWordWrap(True); p.addWidget(note); p.addStretch()
        p=self.page(); row=QHBoxLayout(); self.button(row,self.t("scan"),self.scan_hardware,True); self.button(row,self.t("export"),self.export); p.addLayout(row); self.button(row,self.pair("Dual Boot readiness","جاهزية الإقلاع المزدوج"),self.check_dual_boot,symbol="shield"); self.hardware_panel=self.hardware_view(p)
        if self.inventory:self.show_json(self.hardware_panel,self.inventory.to_dict())
        p=self.page(); form=QFormLayout(); self.iso_path=QLineEdit(); self.iso_path.setReadOnly(True); self.iso_path.setLayoutDirection(Qt.LeftToRight); row=QHBoxLayout(); row.addWidget(self.iso_path); self.button(row,self.t("select"),self.select_iso); form.addRow("ISO",row)
        self.expected_hash=QLineEdit(); self.expected_hash.setPlaceholderText(self.pair("Official SHA256 (optional for analysis only)","SHA256 الرسمي (اختياري للفحص فقط)")); self.expected_hash.setLayoutDirection(Qt.LeftToRight); form.addRow("SHA256",self.expected_hash); p.addLayout(form)
        row=QHBoxLayout(); self.button(row,self.t("analyze"),self.analyze_iso,True); self.button(row,self.pair("Download official ISO","تنزيل ISO رسمي"),self.download_dialog); p.addLayout(row); self.iso_panel=self.text_panel(p)
        self.show_json(self.iso_panel,{"official_sources":CATALOG,"notice":self.pair("Version and size come from your selected image; the catalog does not invent current release numbers.","الإصدار والحجم من صورتك المختارة؛ لا نعرض أرقام إصدارات مفترضة.")})
        p=self.page(); self.profile_form=QFormLayout(); self.fields={}
        for key,label,values in [("distribution",self.pair("Distribution","التوزيعة"),["ubuntu","debian","kali"]),("preset",self.pair("Profile","النمط"),list(PACKAGES)),("locale",self.pair("Language","اللغة"),["en_US.UTF-8","ar_EG.UTF-8"]),("keyboard",self.pair("Keyboard","لوحة المفاتيح"),["us","ara","tr","fr","de","es","it"])]:
            field=QComboBox(); field.addItems(values); field.setLayoutDirection(Qt.LeftToRight); self.fields[key]=field; self.profile_form.addRow(label,field)
        for key,label,value in [("hostname",self.pair("Hostname","اسم الحاسوب"),"smart-os"),("username",self.pair("Username","اسم المستخدم"),"user"),("timezone",self.pair("Timezone","المنطقة الزمنية"),"Africa/Cairo")]:
            field=QLineEdit(value); field.setLayoutDirection(Qt.LeftToRight); self.fields[key]=field; self.profile_form.addRow(label,field)
        p.addLayout(self.profile_form); row=QHBoxLayout(); self.button(row,self.pair("Save profile","حفظ الملف"),self.save_profile); self.button(row,self.pair("Load profile","فتح ملف"),self.load_profile); self.button(row,self.pair("Generate seed","إنشاء إعدادات التثبيت"),self.generate_seed,True); p.addLayout(row)
        card,c=self.card(self.pair("Review storage at boot","راجع الأقسام عند الإقلاع"),self.pair("Generate a seed only after ISO verification. This alpha exports configuration; it does not inject it into an ISO or install a system. Review identity, network and storage in the distribution installer.","أنشئ الإعدادات بعد التحقق من ISO. النسخة تُصدّر ملف إعداد؛ لا تدمجه داخل ISO ولا تثبّت النظام. راجع الهوية والشبكة والأقسام داخل مثبّت التوزيعة.")); p.addWidget(card); p.addStretch()
        p=self.page(); card,c=self.card(self.pair("USB safety preview","معاينة أمان USB"),self.pair("Scan to inspect USB identity and partition protection. Raw writing is available only through the Linux CLI helper after exact confirmation and manual unmounting. Windows USB writing is blocked in this alpha.","افحص هوية USB وحماية أقسامها. الكتابة الخام متاحة فقط من مساعد سطر أوامر Linux بعد تأكيد دقيق وفك التركيب يدويًا. كتابة USB من Windows غير مفعّلة بهذه النسخة.")); p.addWidget(card)
        self.usb_combo=QComboBox(); self.usb_combo.setLayoutDirection(Qt.LeftToRight); p.addWidget(self.usb_combo); row=QHBoxLayout(); self.button(row,self.t("scan"),self.scan_hardware); self.button(row,self.pair("Preview selected USB","معاينة USB المختار"),self.usb_preview,True); p.addLayout(row); self.usb_panel=self.text_panel(p)
        p=self.page(); row=QHBoxLayout(); self.button(row,self.pair("Analyze installer log","تحليل سجل التثبيت"),self.analyze_logs,True); self.button(row,self.pair("Export activity log","تصدير سجل العمليات"),self.export_logs); p.addLayout(row); self.log_panel=self.text_panel(p)
        self.log_panel.setPlainText(self.pair("Local error classification. Suggestions require review; no repair commands run automatically.","تصنيف الأخطاء محليًا. الاقتراحات تحتاج مراجعة؛ لا تُنفّذ أوامر إصلاح تلقائية."))
    def change_language(self,index):
        self.preparation_state={"path":self.iso_path.text(),"hash":self.expected_hash.text(),"fields":{k:v.currentText() if isinstance(v,QComboBox) else v.text() for k,v in self.fields.items()}}
        super().change_language(index)
        self.iso_path.setText(self.preparation_state["path"]); self.expected_hash.setText(self.preparation_state["hash"])
        for key,value in self.preparation_state['fields'].items():
            field=self.fields[key]
            if isinstance(field,QComboBox):field.setCurrentText(value)
            else:field.setText(value)
        if self.iso_report:self.show_json(self.iso_panel,self.iso_report.to_dict())
        if self.inventory:
            for d in self.inventory.disks:
                if d.transport.lower()=="usb":self.usb_combo.addItem(f"{d.path} | {d.model} | {d.size/1024**3:.1f} GiB",d)
    def check_dual_boot(self):
        def done(result):
            self.report['dual_boot_readiness']=result
            dialog=QDialog(self); dialog.setWindowTitle(self.pair("Dual Boot readiness","جاهزية الإقلاع المزدوج")); dialog.resize(760,500)
            layout=QVBoxLayout(dialog); panel=self.text_panel(layout); self.show_json(panel,result)
            self.button(layout,self.pair("Close","إغلاق"),dialog.accept); dialog.exec()
        self.async_task('dual-boot-preflight',dual_boot_readiness,done)
    def scan_hardware(self):
        def done(value):
            self.inventory=value; self.prep_counts[0].setText(value.architecture); self.report["hardware"]=value.to_dict(); self.show_json(self.hardware_panel,value.to_dict()); self.usb_combo.clear()
            for d in value.disks:
                if d.transport.lower()=="usb":self.usb_combo.addItem(f"{d.path} | {d.model} | {d.size/1024**3:.1f} GiB",d)
            self.navigate(1)
        self.async_task("hardware-scan",scan,done)
    def select_iso(self):
        path,_=QFileDialog.getOpenFileName(self,self.t("select"),"","ISO (*.iso)")
        if path:self.iso_path.setText(path)
    def analyze_iso(self):
        if not self.iso_path.text():
            QMessageBox.information(self,self.t("select"),self.pair("Choose an ISO file first.","اختر ملف ISO أولًا.")); return
        path=Path(self.iso_path.text()); expected=self.expected_hash.text().strip() or None
        def done(result):self.iso_report=result; self.prep_counts[1].setText(result.distribution); self.report["iso"]=result.to_dict(); self.show_json(self.iso_panel,result.to_dict())
        self.async_task("iso-analyze",lambda:analyze(path,expected),done)
    def profile(self):
        return InstallationProfile(**{k:v.currentText() if isinstance(v,QComboBox) else v.text() for k,v in self.fields.items()})
    def save_profile(self):
        try:
            profile=self.profile(); profile.validate(); path,_=QFileDialog.getSaveFileName(self,self.t("save"),"installation-profile.json","JSON (*.json)")
            if path:profile.save(Path(path))
        except Exception as exc:QMessageBox.warning(self,self.t("error"),str(exc))
    def load_profile(self):
        path,_=QFileDialog.getOpenFileName(self,self.t("select"),"","JSON (*.json)")
        if not path:return
        try:
            profile=InstallationProfile.load(Path(path))
            for k,v in self.fields.items():
                value=getattr(profile,k)
                if isinstance(v,QComboBox):v.setCurrentText(value)
                else:v.setText(value)
        except Exception as exc:QMessageBox.warning(self,self.t("error"),str(exc))
    def generate_seed(self):
        try:
            if self.iso_report is None:raise ValueError(self.pair("Analyze a verified ISO first.","حلّل ISO متحققًا منه أولًا."))
            name,content=generate(self.profile(),self.iso_report); path,_=QFileDialog.getSaveFileName(self,self.t("save"),name)
            if path:
                if Path(path).resolve()==Path(self.iso_report.path).resolve():raise ValueError("The original ISO cannot be overwritten")
                Path(path).write_text(content,encoding="utf-8"); self.journal.record("seed-export","completed")
        except Exception as exc:QMessageBox.warning(self,self.t("error"),str(exc))
    def usb_preview(self):
        disk=self.usb_combo.currentData()
        if disk is None:
            QMessageBox.information(self,self.t("select"),self.pair("Scan hardware and select a USB drive first.","افحص العتاد ثم اختر ذاكرة USB أولًا.")); return
        iso=self.iso_report
        plan=DiskPlan(disk,"usb",iso.sha256 if iso else "",iso.size if iso else 0); self.show_json(self.usb_panel,plan.preview())
    def analyze_logs(self):
        path,_=QFileDialog.getOpenFileName(self,self.t("select"),"","Logs (*.log *.txt);;All files (*)")
        if not path:return
        def work():
            source=Path(path)
            if source.stat().st_size>8*1024*1024:raise ValueError("Log exceeds 8 MiB")
            from dataclasses import asdict
            return [asdict(f) for f in analyze_log(source.read_text(encoding="utf-8",errors="replace"))]
        def done(findings):self.show_json(self.log_panel,{"findings":findings,"unknown":not bool(findings)})
        self.async_task("log-analysis",work,done)
    def export_logs(self):
        path,_=QFileDialog.getSaveFileName(self,self.t("save"),"smart-linux-activity.jsonl")
        if path:self.journal.export(Path(path))
    def download_dialog(self):
        url,ok=QInputDialog.getText(self,self.pair("Official ISO download","تنزيل ISO رسمي"),self.pair("Official HTTPS ISO URL","رابط ISO رسمي HTTPS"))
        if not ok:return
        checksum,ok=QInputDialog.getText(self,"SHA256",self.pair("Authenticated official checksum","بصمة SHA256 من مصدر رسمي موثوق"))
        if not ok:return
        path,_=QFileDialog.getSaveFileName(self,self.t("save"),"distribution.iso","ISO (*.iso)")
        if not path:return
        def done(result):self.iso_path.setText(path); self.expected_hash.setText(checksum); self.show_json(self.iso_panel,result)
        self.async_task("iso-download",lambda:download_iso(url,checksum,Path(path)),done)

def main():
    import sys
    app=application(); window=LinuxWindow(); window.show()
    if "--self-check" in sys.argv:
        app.processEvents()
        assert window.stack.count() == 6
        window.change_language(1); app.processEvents()
        assert window.layoutDirection() == Qt.RightToLeft
        print("SELF-CHECK PASS: six screens, English/Arabic RTL")
        window.close(); return 0
    return app.exec()
if __name__=="__main__":raise SystemExit(main())
