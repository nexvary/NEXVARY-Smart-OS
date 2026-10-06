from __future__ import annotations
import platform
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QLabel, QLineEdit, QComboBox
from .ui.common import BaseWindow, application
from .ui.panels import metrics
from .ui.icons import icon
from PySide6.QtGui import QColor
from .driver_engine.inventory import inventory, windows_update_drivers
from .driver_engine.backup import backup, restore_preview
from .core.hardware import scan
from .driver_engine.servicing import check_health, list_drivers, image_info
from .driver_engine.machine_profile import export_profile, load_profile
from .core.elevation import request_operation
from .driver_engine.preflight import review_driver

class DriverWindow(BaseWindow):
    def __init__(self,language=None):
        self.devices=[]; self.hardware=None
        super().__init__("driver",language); self.populate(); self.navigate(0)
    def change_language(self,index):
        query=self.device_search.text(); mode=self.device_filter.currentIndex(); selected=self.device_table.currentRow()
        super().change_language(index)
        self.device_search.setText(query); self.device_filter.setCurrentIndex(mode)
        if selected>=0:self.device_table.selectRow(selected)
    def populate(self):
        p=self.page(); card,c=self.card(self.pair("Know every device","اعرف كل جهاز"),self.pair("Inspect real PnP IDs and Device Manager error codes. Back up third-party drivers before formatting Windows. Newer versions are not automatically better.","افحص معرّفات PnP وأكواد أخطاء إدارة الأجهزة. انسخ تعريفات الجهات الخارجية قبل تهيئة Windows. رقم إصدار أعلى لا يعني أنه الأنسب.")); p.addWidget(card)
        self.counts=metrics(p,[(self.pair("Devices","الأجهزة"),"—","#c5e4d0"),(self.pair("Missing drivers","تعريفات ناقصة"),"—","#e7b365"),(self.pair("Needs review","تحتاج مراجعة"),"—","#dc8b8b")])
        self.summary=QLabel(self.pair("No scan yet — no estimated or simulated results.","لم يُنفّذ فحص بعد؛ لا نعرض نتائج تقديرية أو وهمية.")); self.summary.setObjectName("subtitle"); self.summary.setWordWrap(True); p.addWidget(self.summary)
        row=QHBoxLayout(); b=self.button(row,self.pair("Scan devices","فحص الأجهزة"),self.scan_devices,True); b.setEnabled(platform.system()=="Windows"); self.button(row,self.t("backup"),lambda:self.navigate(2)); p.addLayout(row)
        card,c=self.card(self.pair("Restore begins with a review","الاستعادة تبدأ بالمراجعة"),self.pair("Review local driver signatures, catalog payloads and Windows compatibility. Installation awaits recovery validation in a Windows VM.","راجع توقيع التعريف المحلي وملفات الكتالوج والتوافق عبر Windows. التثبيت ينتظر اختبار الاسترداد داخل VM.")); p.addWidget(card)
        if platform.system()!="Windows":self.summary.setText(self.t("notwindows"))
        p.addStretch()
        p=self.page(); row=QHBoxLayout(); b=self.button(row,self.pair("Scan devices","فحص الأجهزة"),self.scan_devices,True); b.setEnabled(platform.system()=="Windows"); self.button(row,self.t("details"),self.device_details); self.button(row,self.t("export"),self.export); self.button(row,self.pair("Review local INF","مراجعة INF محلي"),self.review_local_inf,symbol="shield"); p.addLayout(row)
        filters=QHBoxLayout(); self.device_search=QLineEdit(); self.device_search.setPlaceholderText(self.pair("Search name, manufacturer or Hardware ID…","ابحث بالاسم أو الشركة أو معرّف العتاد…")); self.device_search.textChanged.connect(self.filter_devices); filters.addWidget(self.device_search,1)
        self.device_filter=QComboBox(); self.device_filter.addItems([self.pair("All devices","جميع الأجهزة"),self.pair("Missing drivers","تعريفات ناقصة"),self.pair("Needs review","تحتاج مراجعة"),self.pair("Network rescue","إنقاذ الشبكة")]); self.device_filter.currentIndexChanged.connect(self.filter_devices); filters.addWidget(self.device_filter); p.addLayout(filters)
        self.device_table=QTableWidget(0,5); self.device_table.setHorizontalHeaderLabels([self.pair("Device","الجهاز"),self.pair("Status","الحالة"),"Code",self.pair("Version","الإصدار"),"INF"]); self.device_table.setSelectionBehavior(QTableWidget.SelectRows); self.device_table.setSelectionMode(QTableWidget.SingleSelection); self.device_table.setEditTriggers(QTableWidget.NoEditTriggers); self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents); self.device_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.device_table.doubleClicked.connect(self.device_details); self.device_table.itemSelectionChanged.connect(self.device_details); self.device_table.setAlternatingRowColors(True); self.device_table.verticalHeader().hide(); p.addWidget(self.device_table,1); self.device_panel=self.text_panel(p); self.device_panel.setMaximumHeight(140); self.device_panel.hide()
        p=self.page(); card,c=self.card(self.pair("Driver Store backup","نسخ مخزن التعريفات"),self.pair("Exports third-party OEM drivers with PnPUtil into a new folder, then creates a SHA256 integrity manifest. Microsoft inbox drivers and application installers are not exported. Windows requests administrator permission for this operation only.","يُصدّر تعريفات OEM عبر PnPUtil إلى مجلد جديد ثم ينشئ بيان SHA256 للتحقق. لا يشمل تعريفات Microsoft المدمجة أو برامج الشركات. يطلب Windows صلاحية المسؤول لهذه العملية فقط.")); p.addWidget(card)
        row=QHBoxLayout(); b=self.button(row,self.pair("Back up all OEM drivers","نسخ جميع تعريفات OEM"),self.backup_all,True); b.setEnabled(platform.system()=="Windows"); b=self.button(row,self.pair("Back up selected device","نسخ تعريف الجهاز المختار"),self.backup_selected); b.setEnabled(platform.system()=="Windows"); self.button(row,self.pair("Analyze restore folder","تحليل مجلد الاستعادة"),self.preview_restore); p.addLayout(row); self.backup_panel=self.text_panel(p)
        row=QHBoxLayout(); self.button(row,self.pair("Export offline machine profile","تصدير ملف الجهاز دون إنترنت"),self.export_machine,symbol="chip"); self.button(row,self.pair("Match backup to another machine","مطابقة نسخة لجهاز آخر"),self.match_machine,symbol="search"); p.addLayout(row)
        p=self.page(); card,c=self.card(self.pair("Windows Update candidates","اقتراحات Windows Update"),self.pair("Read-only search for available driver updates through Microsoft's Windows Update API. Results do not prove a driver should replace your current OEM package.","بحث للقراءة فقط عن تعريفات متاحة عبر واجهة Windows Update الرسمية. ظهور تحديث لا يثبت ضرورة استبدال تعريف OEM الحالي.")); p.addWidget(card)
        b=self.button(p,self.pair("Search driver updates","بحث تحديثات التعريفات"),self.search_updates,True); b.setEnabled(platform.system()=="Windows"); self.update_panel=self.text_panel(p)
        p=self.page(); row=QHBoxLayout(); self.button(row,self.t("scan"),self.scan_hardware,True); self.button(row,self.t("export"),self.export); p.addLayout(row); self.hardware_panel=self.hardware_view(p)
        if self.hardware:self.show_json(self.hardware_panel,self.hardware.to_dict())
        p=self.page(); card,c=self.card(self.pair("Windows servicing · Microsoft DISM","خدمة Windows · Microsoft DISM"),self.pair("Read-only tools: check existing corruption flags, list OEM drivers, or inspect a WIM/ESD image. Windows requests permission for the helper only. CheckHealth is not a full scan or repair.","أدوات للقراءة: فحص مؤشرات التلف المسجلة، عرض تعريفات OEM، وتحليل صور WIM/ESD. يطلب Windows الصلاحية للمساعد فقط. CheckHealth لا يجري فحصًا شاملًا أو إصلاحًا.")); p.addWidget(card)
        row=QHBoxLayout()
        for text,callback,symbol in [(self.pair("Check Windows health","فحص حالة Windows"),self.check_windows_health,"shield"),(self.pair("List DISM drivers","تعريفات DISM"),self.inspect_dism_drivers,"driver"),(self.pair("Inspect WIM / ESD","تحليل WIM / ESD"),self.inspect_windows_image,"iso")]:
            b=self.button(row,text,callback,symbol=symbol); b.setEnabled(platform.system()=="Windows")
        p.addLayout(row); exports=QHBoxLayout(); self.button(exports,self.pair("Export activity log","تصدير سجل العمليات"),self.export_logs); self.button(exports,self.t("export"),self.export); p.addLayout(exports); self.log_panel=self.text_panel(p)
        self.log_panel.setPlainText(self.pair("Logs stay on this computer. Diagnostic exports redact hardware identifiers, serials and credentials. Device details remain visible locally.","السجلات محلية. تُحجب معرّفات العتاد والأرقام التسلسلية وبيانات الدخول من التقارير المصدّرة. تفاصيل الأجهزة ظاهرة محليًا."))
        self.render_devices()
    def render_devices(self):
        self.device_table.setRowCount(len(self.devices))
        for row,d in enumerate(self.devices):
            for col,text in enumerate([d.name,self.device_status(d.status),str(d.problem_code),d.version,d.driver_inf]):
                item=QTableWidgetItem(text); item.setToolTip(text); self.device_table.setItem(row,col,item)
                if col==1:item.setForeground(QColor("#e7b365" if d.status=="missing" else "#dc8b8b" if d.status=="needs-review" else "#86ff4a"))
        if self.devices:
            missing=sum(d.status=="missing" for d in self.devices); review=sum(d.status=="needs-review" for d in self.devices)
            for widget,count in zip(self.counts,[len(self.devices),missing,review]):widget.setText(str(count))
            self.summary.setText(self.pair(f"{len(self.devices)} devices  |  {missing} missing  |  {review} need review  |  Outdated: not assessed",f"{len(self.devices)} جهاز  |  {missing} تعريف ناقص  |  {review} يحتاج مراجعة  |  تقادم التعريف: لم يُقيّم"))
        self.filter_devices()
    def device_status(self,status):
        return {"missing":self.pair("Missing","ناقص"),"needs-review":self.pair("Needs review","يحتاج مراجعة"),"installed":self.pair("Installed","مثبّت")}.get(status,status)
    def filter_devices(self,*_):
        if not hasattr(self,"device_table"):return
        query=self.device_search.text().casefold(); mode=self.device_filter.currentIndex()
        for row,d in enumerate(self.devices):
            match=query in " ".join([d.name,d.manufacturer,*d.hardware_ids,*d.compatible_ids]).casefold()
            if mode==1:match=match and d.status=="missing"
            elif mode==2:match=match and d.status=="needs-review"
            elif mode==3:match=match and (d.class_name.casefold()=="net" or any(x.upper().startswith("PCI\\VEN_") and "CC_02" in x.upper() for x in (*d.hardware_ids,*d.compatible_ids)))
            self.device_table.setRowHidden(row,not match)
    def scan_devices(self):
        def done(devices):self.devices=devices; self.report["devices"]=[d.to_dict() for d in devices]; self.render_devices(); self.navigate(1)
        self.async_task("device-inventory",inventory,done)
    def device_details(self,*_):
        index=self.device_table.currentRow()
        if 0<=index<len(self.devices):
            self.device_panel.show(); self.show_json(self.device_panel,self.devices[index].to_dict())
    def review_local_inf(self):
        index=self.device_table.currentRow()
        if index<0 or index>=len(self.devices):QMessageBox.information(self,self.t("select"),self.pair("Select a device first.","اختر جهازًا أولًا.")); return
        path,_=QFileDialog.getOpenFileName(self,self.pair("Choose local driver INF","اختر ملف INF لتعريف محلي"),"","Driver INF (*.inf)")
        if not path:return
        device=self.devices[index]
        def done(result):
            self.report['driver_preflight']=result; self.show_json(self.backup_panel,result); self.navigate(2)
        self.async_task('driver-preflight',lambda:review_driver(Path(path),device),done)
    def destination(self):
        base=QFileDialog.getExistingDirectory(self,self.pair("Choose parent folder for a new backup","اختر المجلد الرئيسي لنسخة احتياطية جديدة"))
        if not base:return None
        from datetime import datetime
        return Path(base)/("Smart-Driver-Backup-"+datetime.now().strftime("%Y%m%d-%H%M%S"))
    def backup_all(self):
        destination=self.destination()
        if destination:self.async_task("driver-backup",lambda:request_operation("driver-backup",{"destination":str(destination.resolve()),"inf":"*"}),lambda r:self.show_json(self.backup_panel,r|{"folder":str(destination)}))
    def backup_selected(self):
        index=self.device_table.currentRow()
        if index<0 or index>=len(self.devices):QMessageBox.information(self,self.t("select"),self.pair("Select a device in Devices first.","اختر جهازًا من صفحة الأجهزة أولًا.")); return
        inf=self.devices[index].driver_inf; destination=self.destination()
        if destination:self.async_task("selected-driver-backup",lambda:request_operation("driver-backup",{"destination":str(destination.resolve()),"inf":inf}),lambda r:self.show_json(self.backup_panel,r|{"folder":str(destination)}))
    def preview_restore(self):
        if not self.devices:QMessageBox.information(self,self.t("select"),self.pair("Scan Windows devices before matching a backup.","افحص أجهزة Windows قبل مطابقة النسخة الاحتياطية.")); return
        path=QFileDialog.getExistingDirectory(self,self.t("select"))
        if path:self.async_task("restore-preview",lambda:restore_preview(Path(path),self.devices),lambda r:self.show_json(self.backup_panel,{"matches":r,"installation":"blocked-in-alpha"}))
    def export_machine(self):
        if not self.devices:QMessageBox.information(self,self.t("select"),self.pair("Scan devices first.","افحص الأجهزة أولًا.")); return
        choice=QMessageBox.question(self,self.pair("Offline machine profile","ملف الجهاز دون إنترنت"),self.pair("The file contains Hardware IDs needed for matching. It is saved locally and is never uploaded. Export?","يحتوي الملف على معرّفات العتاد اللازمة للمطابقة، ويُحفظ محليًا دون رفعه. هل تريد تصديره؟"))
        if choice!=QMessageBox.Yes:return
        path,_=QFileDialog.getSaveFileName(self,self.t("save"),"smart-driver-machine.json","JSON (*.json)")
        if path:
            try:self.show_json(self.backup_panel,export_profile(Path(path),self.devices))
            except Exception as exc:QMessageBox.warning(self,self.t("error"),str(exc))
    def match_machine(self):
        path,_=QFileDialog.getOpenFileName(self,self.pair("Choose machine profile","اختر ملف الجهاز"),"","JSON (*.json)")
        if not path:return
        folder=QFileDialog.getExistingDirectory(self,self.pair("Choose verified driver backup","اختر نسخة التعريفات المتحقق منها"))
        if folder:self.async_task("offline-machine-match",lambda:restore_preview(Path(folder),load_profile(Path(path))),lambda r:self.show_json(self.backup_panel,{"matches":r,"installation":"blocked-in-alpha"}))
    def search_updates(self):self.async_task("windows-update-search",windows_update_drivers,lambda r:self.show_json(self.update_panel,r))
    def scan_hardware(self):
        def done(hardware):self.hardware=hardware; self.report["hardware"]=hardware.to_dict(); self.show_json(self.hardware_panel,hardware.to_dict())
        self.async_task("hardware-scan",scan,done)
    def servicing_done(self,result):
        self.report['servicing']=result; self.show_json(self.log_panel,result)
    def check_windows_health(self):
        self.async_task('dism-check-health',lambda:request_operation('check-health'),self.servicing_done)
    def inspect_dism_drivers(self):
        self.async_task('dism-driver-inspection',lambda:request_operation('list-drivers'),self.servicing_done)
    def inspect_windows_image(self):
        path,_=QFileDialog.getOpenFileName(self,self.pair("Choose Windows image","اختر صورة Windows"),"","Windows image (*.wim *.esd)")
        if path:self.async_task('dism-image-inspection',lambda:request_operation('image-info',{'path':str(Path(path).resolve())}),self.servicing_done)
    def export_logs(self):
        path,_=QFileDialog.getSaveFileName(self,self.t("save"),"smart-driver-activity.jsonl")
        if path:self.journal.export(Path(path))

def main():
    import sys
    app=application(); window=DriverWindow(); window.show()
    if "--native-audit-self-check" in sys.argv:
        import tempfile
        from .driver_engine.native import verify_package
        with tempfile.TemporaryDirectory() as folder:
            inf=Path(folder)/'unsigned.inf';inf.write_text('[Version]\nSignature="$Windows NT$"\nClass=Net\nClassGuid={4d36e972-e325-11ce-bfc1-08002be10318}\nProvider=NEXVARY\nDriverVer=10/06/2026,0.0.0.1\nCatalogFile=unsigned.cat\n')
            (Path(folder)/'unsigned.cat').write_bytes(b'Unsigned test fixture')
            assert not verify_package(inf,'unsigned.cat').verified
        window.close();return 0
    if "--privilege-self-check" in sys.argv:
        result=request_operation('check-health')
        assert result['changes_requested'] is False and result['output']
        window.close(); return 0
    if "--self-check" in sys.argv:
        app.processEvents()
        assert window.stack.count() == 6
        window.change_language(1); app.processEvents()
        assert window.layoutDirection() == Qt.RightToLeft
        print("SELF-CHECK PASS: six screens, English/Arabic RTL")
        window.close(); return 0
    return app.exec()
if __name__=="__main__":raise SystemExit(main())
