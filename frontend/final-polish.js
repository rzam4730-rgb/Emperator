/* Emperator final UI polish: no native dialogs for primary POS flows. */
(function(){
  const toast=(m,t='success')=>window.epToast?window.epToast(m,t):null;
  const alertUi=(m,t='امپراتور')=>window.epAlert?window.epAlert(m,t):Promise.resolve(window.alert(m));
  function patchCheckout(){
    if(typeof window.checkout!=='function'||window.checkout.__epPatched)return;
    const original=window.checkout;
    async function polishedCheckout(){
      if(!Array.isArray(window.cart)||!window.cart.length){await alertUi('ابتدا حداقل یک محصول به سفارش اضافه کنید','ثبت سفارش');return}
      try{await original();}catch(e){await alertUi(e?.message||'ثبت سفارش انجام نشد','خطا در ثبت سفارش')}
    }
    polishedCheckout.__epPatched=true;window.checkout=polishedCheckout;
  }
  function polishButtons(){
    document.querySelectorAll('.primary,.quick button,.report-grid button,.pay-grid button').forEach(b=>b.classList.add('ep-polished-btn'));
    document.querySelectorAll('.panel,.stat-card,.kanban-col,.product').forEach(b=>b.classList.add('ep-polished-card'));
  }
  function boot(){patchCheckout();polishButtons();setTimeout(patchCheckout,500);setTimeout(patchCheckout,1500);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  new MutationObserver(function(){patchCheckout();polishButtons()}).observe(document.body,{childList:true,subtree:true});
})();