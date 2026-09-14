const {app,BrowserWindow} = require('electron');
const {spawn} = require('child_process');
const path=require('path');
let backend;
function startBackend(){
  const exe=app.isPackaged ? path.join(process.resourcesPath,'backend','emperator-backend.exe') : null;
  if(exe) backend=spawn(exe,[],{windowsHide:true});
}
function createWindow(){
  const win=new BrowserWindow({width:1440,height:900,minWidth:1100,minHeight:700,backgroundColor:'#0b0f14',webPreferences:{contextIsolation:true,nodeIntegration:false}});
  win.loadFile(path.join(__dirname,'..','frontend','index.html'));
}
app.whenReady().then(()=>{startBackend();setTimeout(createWindow,1800);});
app.on('before-quit',()=>{if(backend&&!backend.killed) backend.kill();});
app.on('window-all-closed',()=>{if(process.platform!=='darwin') app.quit();});
