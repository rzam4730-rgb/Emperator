// Emperator auth response hardening.
(function(){
  const nativeFetch=window.fetch.bind(window);
  window.fetch=function(input,init){
    try{
      const raw=typeof input==='string'?input:input.url;
      if(location.protocol!=='file:' && raw && raw.indexOf('http://127.0.0.1:8000')===0){
        const u=new URL(raw);
        const target=u.pathname+u.search;
        input=typeof input==='string'?target:new Request(target,input);
      }
    }catch(_){ }
    return nativeFetch(input,init);
  };
  async function readJson(response, context){
    const text=await response.text();
    if(!text.trim()) throw Error(`${context}: سرور پاسخ خالی برگرداند (HTTP ${response.status})`);
    try{return JSON.parse(text)}catch(_){throw Error(`${context}: پاسخ سرور JSON نیست (HTTP ${response.status})`)}
  }
  window.emperatorAuthFix={
    install:function(){
      if(typeof authRequest!=='function')return;
      window.doLogin=async function(phone,password){
        const r=await authRequest('/auth/login',{method:'POST',body:JSON.stringify({phone,password})});
        const d=await readJson(r,'ورود');
        if(!r.ok)throw Error(d.detail||'ورود ناموفق بود');
        await saveTokens(d);
        return getMe();
      };
      window.doRegister=async function(name,phone,password,restaurantName){
        const r=await authRequest('/auth/register',{method:'POST',body:JSON.stringify({name,phone,password,restaurant_name:restaurantName})});
        const d=await readJson(r,'ثبت‌نام');
        if(!r.ok)throw Error(d.detail||'ثبت‌نام ناموفق بود');
        await saveTokens(d);
        return getMe();
      };
      window.refreshAccessToken=async function(){
        if(!refreshToken)return false;
        const r=await fetch(API+'/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:refreshToken})});
        if(!r.ok){accessToken=null;refreshToken=null;localStorage.removeItem('emperator_refresh_token');return false}
        const d=await readJson(r,'تمدید نشست');
        await saveTokens(d);
        return true;
      };
      window.getMe=async function(){
        const r=await authRequest('/auth/me');
        const d=await readJson(r,'بررسی نشست');
        if(!r.ok)throw Error(d.detail||'نشست کاربر معتبر نیست');
        return d;
      };
    }
  };
  window.emperatorAuthFix.install();
})();
