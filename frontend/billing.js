(()=>{
const money=n=>Number(n||0).toLocaleString('fa-IR')+' تومان';
async function pay(type,ref,amount,description,meta={}){
 const base=location.origin; const r=await api('/payments/create',{method:'POST',body:JSON.stringify({payment_type:type,reference_id:ref,amount,gateway:localStorage.getItem('emperator_gateway')||'mock',description,metadata:meta,callback_url:base+'/api/payments/callback/'+(localStorage.getItem('emperator_gateway')||'mock')})});
 if(r.payment_url && r.payment_url.startsWith('http')) location.href=r.payment_url; else alert('پرداخت ایجاد شد. شناسه: '+r.payment_id); return r;
}
async function loadBilling(){
 let page=document.getElementById('billing'); if(!page){page=document.createElement('section');page.id='billing';page.className='page';document.querySelector('.content').appendChild(page)}
 page.innerHTML='<div class="page-head"><div><h1>خرید اعتبار و ماژول‌ها</h1><p>SMS، اعتبار AI و امکانات جانبی امپراتور</p></div></div><div id="billingBox">در حال بارگذاری...</div>';
 try{const [cat,credits,mods,pays]=await Promise.all([api('/billing/catalog'),api('/credits'),api('/billing/modules'),api('/payments')]);
 const active=new Set(mods.map(x=>x.module_code));
 document.getElementById('billingBox').innerHTML=`<div class="usage-grid"><div class="usage-card"><small>اعتبار SMS</small><b>${Number(credits.sms||0).toLocaleString('fa-IR')}</b></div><div class="usage-card"><small>اعتبار AI</small><b>${Number(credits.ai||0).toLocaleString('fa-IR')}</b></div></div><h3>بسته‌های اعتبار</h3><div class="plans-grid">${cat.credit_packs.map(p=>`<div class="plan-card"><h3>${p.name}</h3><div class="price">${money(p.price)}</div><p>${Number(p.credits).toLocaleString('fa-IR')} اعتبار</p><button class="primary" data-buy="${p.code}">خرید</button></div>`).join('')}</div><h3>ماژول‌های جانبی</h3><div class="plans-grid">${cat.modules.map(m=>`<div class="plan-card ${active.has(m.code)?'current':''}"><h3>${m.name}</h3><div class="price">${money(m.price)}</div><p>${active.has(m.code)?'فعال است':'فعال‌سازی ۳۰ روزه'}</p>${active.has(m.code)?'':'<button class="primary" data-module="'+m.code+'">فعال‌سازی</button>'}</div>`).join('')}</div><h3>تراکنش‌های اخیر</h3><div class="sub-events">${pays.map(p=>`<div class="sub-event"><span>${p.payment_type} · ${p.gateway}</span><strong>${money(p.amount)} · ${p.status}</strong></div>`).join('')||'<div class="sub-event">تراکنشی وجود ندارد</div>'}</div>`;
 page.querySelectorAll('[data-buy]').forEach(b=>b.onclick=async()=>{const p=cat.credit_packs.find(x=>x.code===b.dataset.buy);await pay(p.type==='sms'?'sms_credits':'ai_credits',p.code,p.price,p.name,{credits:p.credits})});
 page.querySelectorAll('[data-module]').forEach(b=>b.onclick=async()=>{const p=cat.modules.find(x=>x.code===b.dataset.module);await pay('module',p.code,p.price,p.name,{module_code:p.code})});
 }catch(e){document.getElementById('billingBox').innerHTML='<div class="panel">'+(e.message||'خطا در بارگذاری صورتحساب')+'</div>'}
}
function addNav(){const menu=document.getElementById('moreMenu');if(!menu||menu.querySelector('[data-page="billing"]'))return;const b=document.createElement('button');b.className='nav';b.dataset.page='billing';b.textContent='🧾 خرید و اعتبار';menu.appendChild(b);b.onclick=()=>{showPage('billing');loadBilling()}}
window.addEventListener('load',()=>setTimeout(addNav,150));
})();
