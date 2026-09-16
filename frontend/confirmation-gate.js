/* Emperator confirmation gate: every state-changing business request asks the current user for confirmation. */
(function(){
  const MUTATING=new Set(['POST','PUT','PATCH','DELETE']);
  const AUTH_EXEMPT=/^\/auth\/(login|register|refresh|logout)$/;
  const LABELS={
    '/orders':'ثبت یا تغییر سفارش',
    '/products':'تغییر منوی محصولات',
    '/customers':'تغییر اطلاعات مشتری',
    '/users':'تغییر اطلاعات کاربر یا کارکنان',
    '/inventory':'تغییر موجودی و انبار',
    '/purchases':'ثبت یا تغییر خرید',
    '/recipes':'تغییر دستور پخت',
    '/kds':'تغییر وضعیت آشپزخانه',
    '/accounting':'ثبت یا تغییر عملیات حسابداری',
    '/payments':'انجام عملیات پرداخت',
    '/credits':'تغییر اعتبار',
    '/sms':'ارسال پیامک',
    '/ai':'اجرای عملیات هوش مصنوعی',
    '/subscription':'تغییر اشتراک',
    '/settings':'تغییر تنظیمات'
  };
  function pathOf(input){
    try{const u=new URL(String(input),location.origin);return u.pathname.replace(/^\/api/,'')}catch(_){return String(input||'').split('?')[0]}
  }
  function actionLabel(path,method){
    for(const key of Object.keys(LABELS)) if(path===key||path.startsWith(key+'/')) return LABELS[key];
    return method==='DELETE'?'حذف اطلاعات':'انجام این عملیات';
  }
  function ask(path,method){
    const text='آیا مطمئن هستید که می‌خواهید «'+actionLabel(path,method)+'» را انجام دهید؟';
    if(window.epConfirm)return window.epConfirm(text,'تأیید عملیات');
    return Promise.resolve(window.confirm(text));
  }
  function wrapApi(){
    if(typeof window.api!=='function'||window.api.__epConfirmGate)return;
    const original=window.api;
    async function guarded(path,options={},retry=true){
      const method=String(options?.method||'GET').toUpperCase();
      const pathOnly=pathOf(path);
      if(MUTATING.has(method)&&!AUTH_EXEMPT.test(pathOnly)&&!options.__skipConfirmation){
        const ok=await ask(pathOnly,method);
        if(!ok){
          const e=new Error('عملیات توسط کاربر لغو شد');e.code='USER_CANCELLED';throw e;
        }
      }
      const clean={...options};delete clean.__skipConfirmation;
      return original(path,clean,retry);
    }
    guarded.__epConfirmGate=true;
    guarded.original=original;
    window.api=guarded;
  }
  function wrapFetch(){
    if(window.__emperatorFetchConfirmation)return;
    const original=window.fetch;
    window.fetch=async function(input,init={}){
      const method=String(init?.method||'GET').toUpperCase();
      const path=pathOf(typeof input==='string'?input:(input?.url||''));
      const isApi=path.startsWith('/api/');
      if(isApi&&MUTATING.has(method)&&!AUTH_EXEMPT.test(path.replace(/^\/api/,''))&&!init.__skipConfirmation){
        const ok=await ask(path.replace(/^\/api/,''),method);
        if(!ok){const e=new Error('عملیات توسط کاربر لغو شد');e.code='USER_CANCELLED';throw e;}
      }
      const clean={...init};delete clean.__skipConfirmation;
      return original.call(this,input,clean);
    };
    window.__emperatorFetchConfirmation=true;
  }
  function boot(){wrapApi();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  setTimeout(boot,100);setTimeout(boot,500);setTimeout(boot,1500);
})();
