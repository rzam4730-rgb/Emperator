import os,sys,threading,time,webbrowser
from pathlib import Path
import uvicorn
ROOT=Path(getattr(sys,"_MEIPASS",Path(__file__).resolve().parents[1]))
def run():
 os.chdir(ROOT/"backend");uvicorn.run("app.main:app",host="127.0.0.1",port=8000,log_level="warning")
threading.Thread(target=run,daemon=True).start();time.sleep(2)
webbrowser.open("file:///"+str((ROOT/"frontend"/"index.html").resolve()).replace("\\","/"))
while True: time.sleep(3600)