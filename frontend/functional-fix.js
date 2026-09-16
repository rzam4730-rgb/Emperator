/* Emperator functional patch layer. Loaded last so it can safely override legacy handlers. */
(function(){
  const alertUi=(m,t='امپراتور')=>window.epAlert?window.epAlert(m,t):Promise.resolve(window.alert(m));
  window.checkout=async function(){
    if(!Array.isArray(window.cart)||!window.cart.length){await alertUi('ابتدا حداقل یک محصول به سفارش اضافه کنید','ثبت سفارش');return}
    try{
      const payload={items:window.cart.map(x=>({product_id:x.id,quantity:x.qty})),payment_method:'نقدی'};
      const order=await window.api('/orders',{method:'POST',body:JSON.stringify(payload)});
      window.cart=[];
      if(typeof window.renderCart==='function')window.renderCart();
      if(typeof window.refresh==='function')await window.refresh();
      await alertUi('سفارش شماره '+order.id+' با موفقیت ثبت شد','ثبت سفارش موفق');
    }catch(e){await alertUi(e?.message||'ثبت سفارش انجام نشد','خطا در ثبت سفارش')}
  };
  function wire(){
    const b=document.getElementById('checkoutBtn');
    if(b)b.onclick=window.checkout;
    document.querySelectorAll('#dashboard .page-head .primary,#orders .page-head .primary').forEach(x=>x.onclick=()=>window.showPage&&window.showPage('pos'));
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
})();
