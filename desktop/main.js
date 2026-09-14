const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let backend = null;
let printerBridge = null;

function startProcess(exe, label) {
  const child = spawn(exe, [], { windowsHide: true });
  child.on('error', (err) => console.error(label + ' start failed:', err));
  return child;
}

function startBackend() {
  if (!app.isPackaged) return;
  const exe = path.join(process.resourcesPath, 'backend', 'emperator-backend.exe');
  backend = startProcess(exe, 'Backend');
}

function startPrinterBridge() {
  if (!app.isPackaged) return;
  const exe = path.join(process.resourcesPath, 'printer', 'emperator-printer-bridge.exe');
  printerBridge = startProcess(exe, 'Printer bridge');
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: '#0b0f14',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  const index = app.isPackaged
    ? path.join(process.resourcesPath, 'frontend', 'index.html')
    : path.join(__dirname, '..', 'frontend', 'index.html');

  win.loadFile(index);
}

app.whenReady().then(() => {
  startBackend();
  startPrinterBridge();
  setTimeout(createWindow, 1800);
});

app.on('before-quit', () => {
  if (backend && !backend.killed) backend.kill();
  if (printerBridge && !printerBridge.killed) printerBridge.kill();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
