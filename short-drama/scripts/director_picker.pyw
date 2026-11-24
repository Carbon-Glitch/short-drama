"""Windows folder picker for the installed director desk; no credentials in shortcut URLs."""
from pathlib import Path
import subprocess, sys
from tkinter import Tk, filedialog, messagebox
root=Tk();root.withdraw()
path=filedialog.askdirectory(title="选择短剧项目、集或外部素材目录")
if path:
    cli=Path(__file__).with_name('dashboard_server.py')
    p=subprocess.run([sys.executable,'-B','-X','utf8',str(cli),'--workspace',path,'--open'],capture_output=True,encoding='utf8',errors='replace')
    if p.returncode: messagebox.showerror('导演台未能启动',p.stderr[-1600:])
root.destroy()
