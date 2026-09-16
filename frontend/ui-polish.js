// Emperator Persian UI layer: styled dialogs, toasts, and global error translation.
(function(){
  const messages={
    'Not Found':'صفحه یا بخش موردنظر پیدا نشد.',
    'Unauthorized':'دسترسی شما منقضی شده است. دوباره وارد شوید.',
    'Forbidden':'شما اجازه انجام این عملیات را ندارید.',
    'Bad Request':'اطلاعات واردشده صحیح نیست.',
    'Internal Server Error':'خطای داخلی سامانه رخ داد. دوباره تلاش کنید.',
    'خطا در درخواست':'در ارتباط با سامانه مشکلی پیش آمد. دوباره تلاش کنید.',
    'Failed to fetch':'ارتباط با سرور برقرار نشد. اتصال شبکه و اجرای سامانه را بررسی کنید.',
    'NetworkError when attempting to fetch resource.':'ارتباط با سرور برقرار نشد.',
    'Load failed':'بارگذاری اطلاعات انجام نشد.',
    'Unexpected token':'پاسخ نامعتبر از سامانه دریافت شد.',
    'Invalid credentials':'شماره موبایل یا رمز عبور صحیح نیست.',
    'Authentication required':'برای ادامه باید وارد حساب کاربری شوید.'
  };
  function fa(v){
    let s=String(v??'').trim();
    if(!s)return 'عملیات انجام نشد.';
    if(messages[s])return messages[s];
    if(/^HTTP \d+/.test(s))return 'درخواست با خطا مواجه شد. لطفاً دوباره تلاش کنید.';
    return s;
  }
  function ensure(){
    if(document.getElementById('epToastHost'))return;
    const style=document.createElement('style');style.id='ep-polish-inline';style.textContent=`
      #epToastHost{position:fixed;left:24px;bottom:24px;z-index:99999;display:grid;gap:10px;max-width:380px}
      .ep-toast{direction:rtl;display:flex;align-items:flex-start;gap:12px;padding:14px 16px;border:1px solid var(--line);border-radius:14px;background:var(--panel);color:var(--text);box-shadow:0 16px 40px rgba(0,0,0,.25);animation:epIn .22s ease}
      .ep-toast .ico{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#18212b;flex:none;font-weight:bold}
      .ep-toast b{display:block;margin-bottom:3px}.ep-toast small{color:var(--muted);line-height:1.7}
      #epModal{position:fixed;inset:0;z-index:100000;display:none;place-items:center;background:rgba(4,8,13,.58);backdrop-filter:blur(7px);direction:rtl}
      #epModal.show{display:grid}.ep-modal-card{width:min(470px,calc(100vw - 32px));background:linear-gradient(145deg,var(--panel),var(--panel2));border:1px solid var(--line);border-radius:20px;padding:24px;box-shadow:0 28px 80px rgba(0,0,0,.38);animation:epPop .2s ease}
      .ep-modal-head{display:flex;gap:14px;align-items:center;margin-bottom:18px}.ep-modal-icon{width:48px;height:48px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(135deg,var(--gold),var(--gold2));font-size:23px;color:#18212b}.ep-modal-card h3{margin:0 0 4px;font-size:18px}.ep-modal-card p{margin:0;color:var(--muted);line-height:1.8}.ep-modal-input{width:100%;margin:14px 0 4px;padding:12px 13px;border:1px solid var(--line);border-radius:11px;background:var(--bg2);color:var(--text);font:inherit;outline:none}.ep-modal-input:focus{border-color:var(--gold);box-shadow:0 0 0 3px rgba(232,184,79,.13)}.ep-modal-actions{display:flex;gap:9px;justify-content:flex-start;margin-top:20px}.ep-modal-actions button{min-width:92px;padding:10px 16px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--text);font:inherit;cursor:pointer}.ep-modal-actions .primary{border:0;background:linear-gradient(135deg,var(--gold),var(--gold2));color:#18212b}
      @keyframes epIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}@keyframes epPop{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}
      :root[data-theme="light"] #epModal{background:rgba(22,31,42,.34)}
      @media(max-width:600px){#epToastHost{left:12px;right:12px;bottom:12px;max-width:none}.ep-toast{width:100%}}
    `;document.head.appendChild(style);
    const host=document.createElement('div');host.id='epToastHost';document.body.appendChild(host);
    const modal=document.createElement('div');modal.id='epModal';modal.innerHTML='<div class="ep-modal-card"><div class="ep-modal-head"><div class="ep-modal-icon">♛</div><div><h3 id="epModalTitle">امپراتور</h3><p id="epModalText"></p></div></div><input id="epModalInput" class="ep-modal-input" style="display:none"><div class="ep-modal-actions"><button id="epModalCancel">انصراف</button><button id="epModalOk" class="primary">تأیید</button></div></div>';document.body.appendChild(modal);
  }
  function toast(text,type='info'){ensure();const el=document.createElement('div');el.className='ep-toast';el.innerHTML=`<div class="ico">${type==='error'?'!':type==='success'?'✓':'i'}</div><div><b>${type==='error'?'خطا':type==='success'?'انجام شد':'امپراتور'}</b><small>${escapeHtml(fa(text))}</small></div>`;document.getElementById('epToastHost').appendChild(el);setTimeout(()=>el.remove(),4200)}
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function dialog(kind,title,text,input){ensure();return new Promise(resolve=>{const m=document.getElementById('epModal'),i=document.getElementById('epModalInput');document.getElementById('epModalTitle').textContent=title||'امپراتور';document.getElementById('epModalText').textContent=fa(text);i.style.display=input?'block':'none';i.value=input?.value||'';i.placeholder=input?.placeholder||'';document.getElementById('epModalCancel').style.display=kind==='alert'?'none':'block';m.classList.add('show');if(input)i.focus();else document.getElementById('epModalOk').focus();const done=v=>{m.classList.remove('show');resolve(v)};document.getElementById('epModalOk').onclick=()=>done(input?i.value:true);document.getElementById('epModalCancel').onclick=()=>done(input?null:false);m.onclick=e=>{if(e.target===m)done(input?null:false)}})}
  window.epToast=toast;window.epDialog=dialog;
  window.alert=function(msg){return dialog('alert','پیام امپراتور',msg)};
  window.confirm=function(msg){return dialog('confirm','تأیید عملیات',msg)};
  window.prompt=function(msg,def=''){return dialog('prompt','ورود اطلاعات',msg,{value:def,placeholder:'اطلاعات را وارد کنید'})};
  window.addEventListener('error',e=>{if(e.message)toast(e.message,'error')});
  window.addEventListener('unhandledrejection',e=>{const r=e.reason;toast(r?.message||r?.detail||String(r||'خطای نامشخص'),'error')});
  document.addEventListener('DOMContentLoaded',()=>{ensure();document.querySelectorAll('button').forEach(b=>{b.addEventListener('click',()=>b.classList.add('ep-click'),{passive:true})})});
})();
