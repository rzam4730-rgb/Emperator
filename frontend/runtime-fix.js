// Emperator runtime safety layer: keeps navigation and module actions alive even if an older script fails to initialize.
(function(){
  const API_BASE='http://127.0.0.1:8000/api';
  const nativeFetch=window.fetch.bind(window);
  function authToken(){ try{return window.accessToken||null}catch(_){return null} }
  if(typeof window.api!=='function'){
    window.api=async function(path,options={},retry){
      const headers={'Content-Type':'application/json',...(options.headers||{})};
      const token=authToken();
      if(token)headers.Authorization='Bearer '+token;
      let response=await nativeFetch(API_BASE+path,{...options,headers});
      if(response.status===401 && retry!==false && typeof window.refreshAccessToken==='function'){
        try{ if(await window.refreshAccessToken()){
          const h={'Content-Type':'application/json',...(options.headers||{})};
          const t=authToken(); if(t)h.Authorization='Bearer '+t;
          response=await nativeFetch(API_BASE+path,{...options,headers:h});
        }catch(_){}
      }
      if(!response.ok){let detail='خطا در درخواست';try{const d=await response.json();detail=d.detail||detail}catch(_){}throw Error(detail)}
      const text=await response.text();
      if(!text.trim())return null;
      try{return JSON.parse(text)}catch(_){return text}
    };
  }
  function show(id){
    const target=document.getElementById(id);
    if(!target)return;
    document.querySelectorAll('.page').forEach(p=>p.classList.toggle('active',p===target));
    document.querySelectorAll('.nav[data-page]').forEach(n=>n.classList.toggle('active',n.dataset.page===id));
    const more=document.getElementById('moreMenu');if(more)more.classList.remove('show');
    window.scrollTo(0,0);
    if(id==='inventory' && window.EmperatorInventory && typeof window.EmperatorInventory.load==='function')window.EmperatorInventory.load();
    if(id==='kitchen' && window.EmperatorKDS && typeof window.EmperatorKDS.load==='function')window.EmperatorKDS.load();
  }
  window.emperatorNavigate=show;
  if(typeof window.showPage!=='function')window.showPage=show;
  function wire(){
    document.querySelectorAll('.nav[data-page]').forEach(btn=>{
      if(btn.dataset.runtimeBound)return;
      btn.dataset.runtimeBound='1';
      btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.dataset.page)},true);
    });
    document.querySelectorAll('[data-go]').forEach(btn=>{
      if(btn.dataset.runtimeBound)return;
      btn.dataset.runtimeBound='1';
      btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.dataset.go)},true);
    });
    if(!document.querySelector('.page.active')){
      const first=document.querySelector('.page');if(first)show(first.id);
    }
    const inv=document.getElementById('inventory');
    if(inv && !inv.querySelector('.inv-actions')){
      const head=inv.querySelector('.page-head');
      if(head){const a=document.createElement('div');a.className='inv-actions';a.innerHTML='<button class="primary" data-runtime-inv="add">＋ افزودن ماده اولیه</button><button class="primary" data-runtime-inv="in">📥 ورود کالا</button><button class="textbtn" data-runtime-inv="refresh">↻ بروزرسانی</button>';head.appendChild(a)}
    }
    document.querySelectorAll('[data-runtime-inv]').forEach(b=>{
      if(b.dataset.bound)return;b.dataset.bound='1';
      b.onclick=function(){
        const a=b.dataset.runtimeInv;
        if(a==='add' && window.EmperatorInventory) { window.EmperatorInventory.load(); }
        else if(a==='refresh' && window.EmperatorInventory) window.EmperatorInventory.load();
        else if(a==='in') show('inventory');
      };
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){setTimeout(wire,80)}, {once:true}); else setTimeout(wire,80);
  setTimeout(wire,600);
  setTimeout(wire,1500);
})();
