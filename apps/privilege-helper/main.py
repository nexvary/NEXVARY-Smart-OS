"""No GUI; exactly one validated operation per process."""
import sys
from pathlib import Path
if not getattr(sys,'frozen',False):sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from smart_os.core.elevation import serve

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--pipe',required=True);parser.add_argument('--server-pid',required=True,type=int)
    args=parser.parse_args();serve(args.pipe,args.server_pid);return 0
if __name__=='__main__':raise SystemExit(main())
