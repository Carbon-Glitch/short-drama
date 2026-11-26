"""Small native bootstrap window; the actual workspace opens in the browser."""
from pathlib import Path
import queue
import os
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk

sys.path.insert(0,str(Path(__file__).resolve().parent/'backend'))
from desktop import ensure_service
packaged_skills=Path(__file__).resolve().parent.parent
if (Path(__file__).resolve().parent/'runtime/python').is_dir():
    os.environ.setdefault('DIRECTOR_SKILLS_HOME',str(packaged_skills))

root=tk.Tk();root.title('短剧导演台');root.geometry('420x160');root.resizable(False,False)
root.configure(bg='#f6f3eb')
label=tk.Label(root,text='正在打开导演台…',font=('Microsoft YaHei',13),bg='#f6f3eb',wraplength=380)
label.pack(pady=(28,16))
bar=ttk.Progressbar(root,mode='indeterminate',length=340);bar.pack();bar.start()
updates=queue.Queue()
def start():
    try:updates.put(('ready',ensure_service(status=lambda text:updates.put(('status',text)))))
    except Exception as error:updates.put(('error',str(error)))
def poll():
    try:
        while True:
            kind,value=updates.get_nowait()
            if kind=='ready':webbrowser.open(value);root.destroy();return
            if kind=='error':
                bar.stop();bar.pack_forget();label.config(text=value,font=('Microsoft YaHei',10))
                ttk.Button(root,text='关闭',command=root.destroy).pack();return
            label.config(text=value)
    except queue.Empty:pass
    root.after(100,poll)
threading.Thread(target=start,daemon=True).start();root.after(100,poll);root.mainloop()
