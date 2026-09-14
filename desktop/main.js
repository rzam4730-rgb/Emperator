const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let backend = null;

function startBackend() {
  if (!app.isPackaged) return;
  const exe = path.join(process.resourcesPath, 'backend', 'emperator-backend.exe');
  backend = spawn(exe, [], { windowsHide: true });
  backend.on('error', (err) => console.error('Backend start failed:', err));
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
  setTimeout(createWindow, 1800);
});

app.on('before-quit', () => {
  if (backend && !backend.killed) backend.kill();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
