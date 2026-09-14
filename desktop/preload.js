const {contextBridge}=require('electron');
contextBridge.exposeInMainWorld('emperatorDesktop',{version:'1.0.0'});
