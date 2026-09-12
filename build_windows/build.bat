@echo off
python -m pip install -r backend\requirements.txt
python -m pip install pyinstaller
pyinstaller --noconfirm --onedir --name Emperator --add-data "backend;backend" --add-data "frontend;frontend" desktop\emperor_desktop.py
