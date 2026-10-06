from __future__ import annotations
import platform
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QLabel
from .ui.common import BaseWindow, application
from .driver_engine.inventory import inventory, windows_update_drivers
from .driver_engine.backup import backup, restore_preview
from .core.hardware import scan

class DriverWindow(BaseWindow):
    def __init__(self,language="en"):
        self.devices=[]; self.hardware=None
        super().__init__("driver",language); self.populate(); self.navigate(0)
    def populate(self):
        p=self.page(); card,c=self.card(self.pair("Know every device","اعرف كل جهاز"),self.pair("Inspect real PnP IDs and Device Manager error codes. Back up third-party drivers before formatting Windows. Newer versions are not automatically better.","افحص معرّفات PnP وأكواد أخطاء إدارة الأجهزة. انسخ تعريفات الجهات الخارجية قبل تهيئة Windows. رقم إصدار أعلى لا يعني أنه الأنسب.")); p.addWidget(card)
        self.summary=QLabel(self.pair("No scan yet — no estimated or simulated results.","لم يُنفّذ فحص بعد؛ لا نعرض نتائج تقديرية أو وهمية.")); self.summary.setObjectName("subtitle"); self.summary.setWordWrap(True); p.addWidget(self.summary)
        row=QHBoxLayout(); b=self.button(row,self.pair("Scan devices","فحص الأجهزة"),self.scan_devices,True); b.setEnabled(platform.system()=="Windows"); self.button(row,self.t("backup"),lambda:self.navigate(2)); p.addLayout(row)
        card,c=self.card(self.pair("Restore begins with a review","الاستعادة تبدأ بالمراجعة"),self.pair("This alpha verifies backup hashes and proposes matching INF candidates. Installation is blocked until catalog membership, OS compatibility, recovery and rollback pass Windows VM tests.","تتحقق النسخة من بصمات النسخة الاحتياطية وتقترح ملفات INF المطابقة. تثبيت التعريفات محظور حتى اختبار توقيع الحزمة وتوافق النظام والاستعادة والتراجع داخل Windows.")); p.addWidget(card)
        if platform.system()!="Windows":
            card,c=self.card(self.pair("Windows required","يتطلب Windows"),self.t("notwindows")); p.addWidget(card)
        p.addStretch()
        p=self.page(); row=QHBoxLayout(); b=self.button(row,self.pair("Scan devices","فحص الأجهزة"),self.scan_devices,True); b.setEnabled(platform.system()=="Windows"); self.button(row,self.t("details"),self.device_details); self.button(row,self.t("export"),self.export); p.addLayout(row)
        self.device_table=QTableWidget(0,5); self.device_table.setHorizontalHeaderLabels([self.pair("Device","الجهاز"),self.pair("Status","الحالة"),"Code",self.pair("Version","الإصدار"),"INF"]); self.device_table.setSelectionBehavior(QTableWidget.SelectRows); self.device_table.setSelectionMode(QTableWidget.SingleSelection); self.device_table.setEditTriggers(QTableWidget.NoEditTriggers); self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.device_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.device_table.doubleClicked.connect(self.device_details); p.addWidget(self.device_table,1); self.device_panel=self.text_panel(p); self.device_panel.setMaximumHeight(180)
        p=self.page(); card,c=self.card(self.pair("Driver Store backup","نسخ مخزن التعريفات"),self.pair("Exports third-party OEM drivers with PnPUtil into a new folder, then creates a SHA256 integrity manifest. Microsoft inbox drivers and application installers are not exported. Export may require administrator permission.","يُصدّر تعريفات OEM عبر PnPUtil إلى مجلد جديد ثم ينشئ بيان SHA256 للتحقق. لا يشمل تعريفات Microsoft المدمجة أو برامج الشركات. قد يتطلب التصدير صلاحية المسؤول.")); p.addWidget(card)
        row=QHBoxLayout(); b=self.button(row,self.pair("Back up all OEM drivers","نسخ جميع تعريفات OEM"),self.backup_all,True); b.setEnabled(platform.system()=="Windows"); b=self.button(row,self.pair("Back up selected device","نسخ تعريف الجهاز المختار"),self.backup_selected); b.setEnabled(platform.system()=="Windows"); self.button(row,self.pair("Analyze restore folder","تحليل مجلد الاستعادة"),self.preview_restore); p.addLayout(row); self.backup_panel=self.text_panel(p)
        p=self.page(); card,c=self.card(self.pair("Windows Update candidates","اقتراحات Windows Update"),self.pair("Read-only search for available driver updates through Microsoft's Windows Update API. Results do not prove a driver should replace your current OEM package.","بحث للقراءة فقط عن تعريفات متاحة عبر واجهة Windows Update الرسمية. ظهور تحديث لا يثبت ضرورة استبدال تعريف OEM الحالي.")); p.addWidget(card)
        b=self.button(p,self.pair("Search driver updates","بحث تحديثات التعريفات"),self.search_updates,True); b.setEnabled(platform.system()=="Windows"); self.update_panel=self.text_panel(p)
        p=self.page(); row=QHBoxLayout(); self.button(row,self.t("scan"),self.scan_hardware,True); self.button(row,self.t("export"),self.export); p.addLayout(row); self.hardware_panel=self.text_panel(p)
        if self.hardware:self.show_json(self.hardware_panel,self.hardware.to_dict())
        p=self.page(); self.button(p,self.pair("Export activity log","تصدير سجل العمليات"),self.export_logs); self.log_panel=self.text_panel(p)
        self.log_panel.setPlainText(self.pair("Logs stay on this computer. Diagnostic exports redact hardware identifiers, serials and credentials. Device details remain visible locally.","السجلات محلية. تُحجب معرّفات العتاد والأرقام التسلسلية وبيانات الدخول من التقارير المصدّرة. تفاصيل الأجهزة ظاهرة محليًا."))
        self.render_devices()
    def render_devices(self):
        self.device_table.setRowCount(len(self.devices))
        for row,d in enumerate(self.devices):
            for col,text in enumerate([d.name,d.status,str(d.problem_code),d.version,d.driver_inf]):
                item=QTableWidgetItem(text); item.setToolTip(text); self.device_table.setItem(row,col,item)
        if self.devices:
            missing=sum(d.status=="missing" for d in self.devices); review=sum(d.status=="needs-review" for d in self.devices)
            self.summary.setText(self.pair(f"{len(self.devices)} devices  |  {missing} missing  |  {review} need review  |  Outdated: not assessed",f"{len(self.devices)} جهاز  |  {missing} تعريف ناقص  |  {review} يحتاج مراجعة  |  تقادم التعريف: لم يُقيّم"))
    def scan_devices(self):
        def done(devices):self.devices=devices; self.report["devices"]=[d.to_dict() for d in devices]; self.render_devices(); self.navigate(1)
        self.async_task("device-inventory",inventory,done)
    def device_details(self,*_):
        index=self.device_table.currentRow()
        if 0<=index<len(self.devices):self.show_json(self.device_panel,self.devices[index].to_dict())
    def destination(self):
        base=QFileDialog.getExistingDirectory(self,self.pair("Choose parent folder for a new backup","اختر المجلد الرئيسي لنسخة احتياطية جديدة"))
        if not base:return None
        from datetime import datetime
        return Path(base)/("Smart-Driver-Backup-"+datetime.now().strftime("%Y%m%d-%H%M%S"))
    def backup_all(self):
        destination=self.destination()
        if destination:self.async_task("driver-backup",lambda:backup(destination),lambda r:self.show_json(self.backup_panel,r|{"folder":str(destination)}))
    def backup_selected(self):
        index=self.device_table.currentRow()
        if index<0 or index>=len(self.devices):QMessageBox.information(self,self.t("select"),self.pair("Select a device in Devices first.","اختر جهازًا من صفحة الأجهزة أولًا.")); return
        inf=self.devices[index].driver_inf; destination=self.destination()
        if destination:self.async_task("selected-driver-backup",lambda:backup(destination,inf),lambda r:self.show_json(self.backup_panel,r|{"folder":str(destination)}))
    def preview_restore(self):
        if not self.devices:QMessageBox.information(self,self.t("select"),self.pair("Scan Windows devices before matching a backup.","افحص أجهزة Windows قبل مطابقة النسخة الاحتياطية.")); return
        path=QFileDialog.getExistingDirectory(self,self.t("select"))
        if path:self.async_task("restore-preview",lambda:restore_preview(Path(path),self.devices),lambda r:self.show_json(self.backup_panel,{"matches":r,"installation":"blocked-in-alpha"}))
    def search_updates(self):self.async_task("windows-update-search",windows_update_drivers,lambda r:self.show_json(self.update_panel,r))
    def scan_hardware(self):
        def done(hardware):self.hardware=hardware; self.report["hardware"]=hardware.to_dict(); self.show_json(self.hardware_panel,hardware.to_dict())
        self.async_task("hardware-scan",scan,done)
    def export_logs(self):
        path,_=QFileDialog.getSaveFileName(self,self.t("save"),"smart-driver-activity.jsonl")
        if path:self.journal.export(Path(path))

def main():
    import sys
    app=application(); window=DriverWindow(); window.show()
    if "--self-check" in sys.argv:
        app.processEvents()
        assert window.stack.count() == 6
        window.change_language(1); app.processEvents()
        assert window.layoutDirection() == Qt.RightToLeft
        print("SELF-CHECK PASS: six screens, English/Arabic RTL")
        window.close(); return 0
    return app.exec()
if __name__=="__main__":raise SystemExit(main())
