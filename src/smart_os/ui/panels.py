"""Readable local reports. All values are escaped before display."""
from html import escape
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTextBrowser, QTableWidget, QTableWidgetItem, QHeaderView

LABELS={
 'health_verified':('Health verified','سلامة النظام متحقق منها'),'health_state':('Component health','حالة المكونات'),'verification':('Verification','التحقق'),'exit_code':('Exit code','كود النتيجة'),'exit_code_hex':('Exit code (hex)','كود النتيجة السداسي'),'reboot_required':('Restart required','إعادة التشغيل مطلوبة'),'automatic_reboot':('Automatic restart','إعادة تشغيل تلقائية'),'analysis_before':('Analysis before cleanup','التحليل قبل التنظيف'),'analysis_after':('Analysis after cleanup','التحليل بعد التنظيف'),'reset_base':('ResetBase enabled','تفعيل ResetBase'),'source':('Source','المصدر'),'error_output':('Error output','تفاصيل الخطأ'),
 'trust':('Package trust','موثوقية الحزمة'),'trust_verified':('Trust verified','التحقق من الثقة'),'native_compatible':('Windows compatible','توافق Windows'),'native_candidates':('Windows driver candidates','التعريفات المتوافقة حسب Windows'),'native_rank':('Windows rank (lower is better)','ترتيب Windows (الأقل أفضل)'),'preflight_passed':('Preflight passed','اجتياز الفحص الأولي'),'plan_digest':('Plan SHA256','بصمة خطة المراجعة'),'recovery':('Recovery readiness','جاهزية الاسترداد'),'backup_required':('Backup required','نسخة احتياطية مطلوبة'),'restore_point':('Restore point','نقطة الاستعادة'),'rollback':('Rollback','التراجع'),'verified':('Verified','تم التحقق'),'files_verified':('Verified payload files','ملفات الحزمة المتحقق منها'),'signer':('Digital signer','الموقّع الرقمي'),'catalog':('Catalog','الكتالوج'),'match':('ID match','مطابقة المعرّف'),
 'tool':('Tool','الأداة'),'operation':('Operation','العملية'),'scope':('Scope','نطاق الفحص'),'changes_requested':('Changes requested','تغييرات مطلوبة'),'output':('Command output','نتيجة الأمر'),
 'checks':('Readiness checks','فحوص الجاهزية'),'check':('Check','الفحص'),'state':('Result','النتيجة'),'value':('Observed value','القيمة المكتشفة'),'action':('Next step','الخطوة التالية'),'ready_to_partition':('Ready to partition','جاهز لتعديل الأقسام'),'automatic_changes':('Automatic changes','تغييرات تلقائية'),'class_name':('Device class','فئة الجهاز'),'checksum_status':('Checksum status','حالة البصمة'),'release_label':('Release label','اسم الإصدار'),'warnings':('Warnings','تنبيهات'),
 'system':('Operating system','نظام التشغيل'),'architecture':('Architecture','المعمارية'),
 'cpu':('Processor','المعالج'),'memory_bytes':('Memory','الذاكرة'), 'boot_mode':('Boot mode','وضع الإقلاع'),
 'secure_boot':('Secure Boot','الإقلاع الآمن'),'disks':('Storage','الأقراص'), 'devices':('Devices','الأجهزة'),
 'limitations':('Checks still needed','فحوص لازمة'), 'path':('Path','المسار'), 'model':('Model','الطراز'),
 'size':('Size','الحجم'),'filesystem':('Filesystem','نظام الملفات'),'kind':('Type','النوع'),
 'transport':('Connection','التوصيل'),'readonly':('Read only','للقراءة فقط'), 'partitions':('Partitions','الأقسام'),
 'sha256':('SHA256','SHA256'),'distribution':('Distribution','التوزيعة'),'installer':('Installer','المثبّت'),
 'version':('Version','الإصدار'),'uefi':('UEFI','UEFI'),'legacy':('Legacy boot','الإقلاع التقليدي'),
 'checksum_verified':('Checksum verified','التحقق من البصمة'),'name':('Device','الجهاز'),
 'hardware_ids':('Hardware IDs','معرّفات العتاد'),'compatible_ids':('Compatible IDs','معرّفات التوافق'),
 'manufacturer':('Manufacturer','الشركة المصنّعة'),'provider':('Provider','المزوّد'), 'driver_inf':('Driver INF','ملف INF'),
 'status':('Status','الحالة'),'problem_code':('Device Manager code','كود إدارة الأجهزة'),
 'packages':('Packages','الحزم'),'files':('Files','الملفات'),'folder':('Folder','المجلد'),
 'candidate':('Candidate','التعريف المقترح'),'matches':('Matching drivers','التعريفات المطابقة'),
 'candidates':('Candidates','الاقتراحات'),'eligible':('Eligible','مؤهل'), 'reason':('Reason','السبب'),
 'findings':('Findings','نتائج التشخيص'),'suggestion':('Suggested action','الإجراء المقترح'),
 'severity':('Severity','الخطورة'),'message':('Message','الرسالة'),'installation':('Installation','التثبيت'),
}

def label(key,language): return LABELS.get(key,(key.replace('_',' ').title(),key.replace('_',' ')))[language=='ar']

def value_text(value,language,key=''):
    if value is None:return 'لم يُفحص' if language=='ar' else 'Not checked'
    if isinstance(value,bool):return ('نعم' if value else 'لا') if language=='ar' else ('Yes' if value else 'No')
    if key in {'memory_bytes','size'} and isinstance(value,(int,float)):return f'{value/1024**3:.1f} GiB'
    translations={'completed':'اكتملت العملية','failed':'فشلت العملية','indeterminate':'النتيجة غير محسومة','verification-failed':'فشل التحقق بعد التنفيذ','blocked':'لم يبدأ التنفيذ','not-run':'لم يُنفّذ','healthy':'سليم','repairable':'قابل للإصلاح','non-repairable':'غير قابل للإصلاح','Exact hardware ID':'مطابقة معرّف العتاد بدقة','Compatible ID only; explicit OEM review is required':'مطابقة معرّف توافق فقط؛ يلزم مراجعة توافق الشركة المصنّعة','Windows found no compatible driver for the current OS and device':'لم يجد Windows تعريفًا متوافقًا مع النظام الحالي والجهاز','Sensitive driver class needs a separately validated recovery workflow':'فئة تعريف حساسة تتطلب مسار استرداد مختبرًا بصورة مستقلة','Driver package changed during review; review again':'تغيّرت حزمة التعريف أثناء المراجعة؛ أعد الفحص','Signature, payload membership, exact Hardware ID and native Windows compatibility passed; installation/rollback VM gate remains pending':'اجتاز التوقيع وملفات الكتالوج والمطابقة والتوافق عبر Windows الفحص؛ التثبيت والتراجع ينتظران اختبار VM','not-created':'لم تُنشأ','not-validated':'لم يُختبر','Existing corruption flags only; not a full scan or repair':'مؤشرات التلف المسجلة فقط؛ دون فحص شامل أو إصلاح','passed':'اجتاز الفحص','review':'يحتاج مراجعة','unknown':'غير معروف','boot-mode':'وضع الإقلاع','fast-startup':'بدء التشغيل السريع','bitlocker':'تشفير BitLocker','partition-space':'مساحة الأقسام','windows-state':'حالة Windows','blocked-in-alpha':'غير مفعّل في النسخة الأولية',
    'Use installation media matching the current boot mode.':'استخدم وسيط تثبيت متوافقًا مع وضع الإقلاع الحالي.',
    'Disable Fast Startup manually in Windows before accessing Windows volumes from Linux.':'عطّل بدء التشغيل السريع يدويًا في Windows قبل الوصول إلى أقسامه من Linux.',
    'Check encryption and obtain a recovery key manually. No encryption settings are changed.':'راجع التشفير واحتفظ بمفتاح الاسترداد يدويًا. لا يغيّر البرنامج إعدادات التشفير.',
    'Keep a verified recovery key. Review encrypted disks before partition changes; encryption is never disabled automatically.':'احتفظ بمفتاح استرداد متحقق منه. راجع الأقراص المشفّرة قبل تعديل الأقسام؛ لا يُعطّل التشفير تلقائيًا.',
    'Verify EFI, recovery partitions and actual unallocated space in the installation disk preview. Filesystem free space is not unallocated space.':'راجع أقسام EFI والاسترداد والمساحة غير المخصصة في معاينة القرص. المساحة الفارغة داخل قسم تختلف عن المساحة غير المخصصة.',
    'Run this check inside Windows. Linux cannot reliably determine Windows Fast Startup or BitLocker protection.':'شغّل هذا الفحص من Windows. لا يستطيع Linux تحديد حالة بدء التشغيل السريع وحماية BitLocker بصورة موثوقة.'}
    return translations.get(str(value),str(value)) if language=='ar' else str(value)

class ReportPanel(QTextBrowser):
    def __init__(self,language='en'):
        super().__init__(); self.language=language; self.last_data=None; self.setOpenExternalLinks(False); self.setOpenLinks(False)
    def display(self,value):
        self.last_data=value; language=self.language
        def render(data,depth=0):
            if isinstance(data,dict):
                rows=[]
                for key,val in data.items():
                    if key=='serial':continue
                    content=render(val,depth+1) if isinstance(val,(dict,list,tuple)) else escape(value_text(val,language,key))
                    if key=='output' and isinstance(val,str):content='<pre dir="ltr" style="white-space:pre-wrap">'+escape(val)+'</pre>'
                    rows.append(f'<tr><td width="28%" style="color:#a9c6b0;padding:8px">{escape(label(key,language))}</td><td style="padding:8px"><span dir="auto">{content}</span></td></tr>')
                return '<table width="100%" cellspacing="0">'+''.join(rows)+'</table>'
            if isinstance(data,(list,tuple)):
                if not data:return 'لا توجد عناصر' if language=='ar' else 'No items'
                result='<br/>'.join(render(item,depth+1) for item in data[:200])
                if len(data)>200:result+=f'<p>{len(data)-200} '+('عنصر إضافي في التقرير المصدّر' if language=='ar' else 'more items in exported report')+'</p>'
                return result
            return escape(value_text(data,language))
        direction='rtl' if language=='ar' else 'ltr'
        self.setHtml(f'<html><body dir="{direction}" style="font-family:Noto Sans Arabic,sans-serif;font-size:13px;color:#edf5ee">{render(value)}</body></html>')

def metrics(layout,items):
    row=QHBoxLayout(); result=[]
    for title,value,color in items:
        card=QFrame(); card.setObjectName('card'); col=QVBoxLayout(card); col.setContentsMargins(16,12,16,12)
        number=QLabel(str(value)); number.setObjectName('metric'); number.setStyleSheet(f'color:{color}'); number.setLayoutDirection(Qt.LeftToRight)
        caption=QLabel(title); caption.setObjectName('metriclabel'); caption.setWordWrap(True); caption.setMinimumHeight(32)
        col.addWidget(number); col.addWidget(caption); row.addWidget(card,1); result.append(number)
    layout.addLayout(row); return result

class HardwarePanel(QWidget):
    def __init__(self,language='en'):
        super().__init__(); self.language=language; self.last_data=None; self.layout_=QVBoxLayout(self); self.layout_.setContentsMargins(0,0,0,0)
        self.facts=ReportPanel(language); self.facts.setMaximumHeight(240); self.layout_.addWidget(self.facts)
        self.table=QTableWidget(0,4); self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setHorizontalHeaderLabels(['القرص / الطراز','السعة','التوصيل','الحماية'] if language=='ar' else ['Disk / model','Capacity','Connection','Protection'])
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch)
        for i in range(1,4):self.table.horizontalHeader().setSectionResizeMode(i,QHeaderView.ResizeToContents)
        self.layout_.addWidget(self.table,1); self.facts.setPlainText('نفّذ الفحص لعرض بيانات هذا الجهاز.' if language=='ar' else 'Scan to display this machine’s hardware.')
    def display(self,data):
        self.last_data=data; facts={k:v for k,v in data.items() if k not in {'disks','devices'}}; self.facts.display(facts)
        self.table.setRowCount(len(data.get('disks',[])))
        for row,d in enumerate(data.get('disks',[])):
            protected=any(p['kind'] in {'windows','efi','recovery','oem','unknown','data'} for p in d.get('partitions',[]))
            protection=('محمي؛ راجع الأقسام' if protected else 'يلزم مراجعة الأقسام') if self.language=='ar' else ('Protected; review partitions' if protected else 'Partition review required')
            for col,text in enumerate([d['model'] or d['path'],value_text(d['size'],self.language,'size'),d['transport'],protection]):
                item=QTableWidgetItem(text); item.setToolTip(d['path'] if col==0 else text); self.table.setItem(row,col,item)
