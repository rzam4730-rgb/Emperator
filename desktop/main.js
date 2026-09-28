const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
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

function checkBackendHealth() {
  return new Promise((resolve) => {
    const request = http.get('http://127.0.0.1:8000/api/health', (response) => {
      response.resume();
      resolve(response.statusCode === 200);
    });
    request.setTimeout(1500, () => {
      request.destroy();
      resolve(false);
    });
    request.on('error', () => resolve(false));
  });
}

async function waitForBackend(timeoutMs = 30000) {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    if (await checkBackendHealth()) return true;
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  return false;
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

app.whenReady().then(async () => {
  startBackend();
  startPrinterBridge();
  const ready = await waitForBackend();
  if (!ready) {
    console.error('Backend did not become ready within 30 seconds.');
    app.quit();
    return;
  }
  createWindow();
});

app.on('before-quit', () => {
  if (backend && !backend.killed) backend.kill();
  if (printerBridge && !printerBridge.killed) printerBridge.kill();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
