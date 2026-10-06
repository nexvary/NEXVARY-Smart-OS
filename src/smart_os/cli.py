from __future__ import annotations
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from .core.hardware import scan, scan_disks
from .core.safety import DiskPlan
from .installer_engine.iso import analyze
from .installer_engine.profiles import InstallationProfile
from .distro_adapters.config import generate

def main(argv=None):
    p=argparse.ArgumentParser(prog="smart-os",description="SMART OS local diagnostics and preparation")
    sub=p.add_subparsers(dest="command",required=True)
    sub.add_parser("hardware")
    a=sub.add_parser("iso"); a.add_argument("path",type=Path); a.add_argument("--sha256")
    a=sub.add_parser("seed"); a.add_argument("profile",type=Path); a.add_argument("iso",type=Path); a.add_argument("--sha256",required=True); a.add_argument("--output",type=Path,required=True)
    sub.add_parser("devices")
    a=sub.add_parser("driver-backup"); a.add_argument("destination",type=Path); a.add_argument("--inf",default="*")
    a=sub.add_parser("restore-preview"); a.add_argument("directory",type=Path)
    a=sub.add_parser("usb-preview"); a.add_argument("disk"); a.add_argument("iso",type=Path); a.add_argument("--sha256",required=True)
    a=sub.add_parser("usb-write"); a.add_argument("plan",type=Path); a.add_argument("iso",type=Path); a.add_argument("--confirm",required=True)
    a=sub.add_parser("analyze-log"); a.add_argument("path",type=Path)
    args=p.parse_args(argv)
    try:
        if args.command=="hardware":result=scan().to_dict()
        elif args.command=="iso":result=analyze(args.path,args.sha256).to_dict()
        elif args.command=="seed":
            if args.output.exists():raise ValueError("Output exists; choose a new path")
            name,content=generate(InstallationProfile.load(args.profile),analyze(args.iso,args.sha256)); args.output.write_text(content,encoding="utf-8"); result={"file":str(args.output),"format":name,"disk_changes":False}
        elif args.command=="devices":
            from .driver_engine.inventory import inventory
            result=[d.to_dict() for d in inventory()]
        elif args.command=="driver-backup":
            from .driver_engine.backup import backup
            result=backup(args.destination,args.inf)
        elif args.command=="restore-preview":
            from .driver_engine.backup import restore_preview
            from .driver_engine.inventory import inventory
            result=restore_preview(args.directory,inventory())
        elif args.command=="usb-preview":
            report=analyze(args.iso,args.sha256); disk=next((d for d in scan_disks() if d.path==args.disk),None)
            if disk is None:raise ValueError("Disk not found")
            result=DiskPlan(disk,"usb",report.sha256,report.size).preview()
        elif args.command=="usb-write":
            from .core.hardware import Disk, Partition
            from .installer_engine.usb import write_usb
            raw=json.loads(args.plan.read_text()); d=raw["target"]; d["partitions"]=tuple(Partition(**p) for p in d["partitions"])
            plan=DiskPlan(Disk(**d),"usb",raw["image_sha256"],raw["image_size"])
            result=write_usb(plan,args.iso,args.confirm)
        else:
            from .core.diagnostics import analyze_log
            if args.path.stat().st_size>8*1024*1024:raise ValueError("Log exceeds 8 MiB")
            result=[asdict(f) for f in analyze_log(args.path.read_text(errors="replace"))]
        print(json.dumps(result,indent=2,ensure_ascii=False)); return 0
    except Exception as exc:
        print(json.dumps({"error":str(exc),"success":False},ensure_ascii=False)); return 2
if __name__=="__main__":raise SystemExit(main())
