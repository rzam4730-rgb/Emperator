(()=>{
const money=n=>Number(n||0).toLocaleString('fa-IR')+' تومان';
const pct=(u,l)=>l>0?Math.min(100,Math.round(u/l*100)):0;
function addSubscriptionNav(){
 const menu=document.getElementById('moreMenu'); if(!menu||document.querySelector('[data-page="subscription"]'))return;
 const b=document.createElement('button'); b.className='nav'; b.dataset.page='subscription'; b.textContent='💳 اشتراک و صورتحساب'; menu.appendChild(b);
 b.onclick=()=>showSubscription();
 const s=document.createElement('section'); s.className='page'; s.id='subscription';
 s.innerHTML=`<div class="page-head"><div><h1>اشتراک و صورتحساب</h1><p>مدیریت پلن، اعتبارها و میزان مصرف امپراتور</p></div><button class="primary" id="renewSub">↻ تمدید اشتراک</button></div><div id="subContent">در حال بارگذاری...</div>`;
 document.querySelector('.content').appendChild(s);
 const st=document.createElement('style'); st.textContent=`#subscription .sub-hero{display:flex;justify-content:space-between;gap:20px;align-items:center;background:linear-gradient(135deg,#17263a,#111a27);border:1px solid #2b3d52;border-radius:18px;padding:24px;margin-bottom:18px}#subscription .sub-hero h2{margin:0 0 7px;color:#f2c85d}#subscription .sub-hero p{margin:0;color:#9eafc1}#subscription .sub-badge{padding:8px 13px;border-radius:999px;background:#173d2a;color:#55d68a;font-size:12px}#subscription .usage-grid,#subscription .plans-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}#subscription .usage-card,#subscription .plan-card{background:#151f2c;border:1px solid #2b3d52;border-radius:14px;padding:18px}#subscription .usage-card small{color:#93a4b7}#subscription .usage-card b{display:block;font-size:20px;margin:7px 0}.meter{height:8px;background:#263446;border-radius:99px;overflow:hidden}.meter i{display:block;height:100%;background:#e5b94f}.plan-card h3{margin:0 0 8px}.plan-card .price{font-size:20px;font-weight:700}.plan-card ul{padding-right:18px;color:#a8b7c7;line-height:2;font-size:12px}.plan-card.current{border-color:#d8b24f;box-shadow:0 0 0 1px #d8b24f33}.plan-card button{width:100%;margin-top:8px}.sub-section-title{margin:22px 0 12px}.sub-events{background:#151f2c;border:1px solid #2b3d52;border-radius:14px;padding:6px 18px}.sub-event{display:flex;justify-content:space-between;padding:13px 0;border-bottom:1px solid #243244;color:#b9c5d1}.sub-event:last-child{border:0}@media(max-width:900px){#subscription .usage-grid,#subscription .plans-grid{grid-template-columns:1fr 1fr}#subscription .sub-hero{flex-direction:column;align-items:flex-start}}`;
 document.head.appendChild(st); document.getElementById('renewSub').onclick=renewSubscription;
}
async function showSubscription(){addSubscriptionNav();showPage('subscription');await loadSubscription();}
async function loadSubscription(){
 const box=document.getElementById('subContent'); if(!box)return;
 try{const [s,plans,events]=await Promise.all([api('/subscription'),api('/plans'),api('/subscription/events')]);
 const u=s.usage||{}, l=s.limits||{};
 box.innerHTML=`<div class="sub-hero"><div><h2>پلن ${s.plan_name}</h2><p>تا ${new Date(s.expires_at).toLocaleDateString('fa-IR')} معتبر است · ${s.auto_renew?'تمدید خودکار فعال':'تمدید خودکار خاموش'}</p></div><span class="sub-badge">${s.status==='active'?'فعال':'منقضی'}</span></div><div class="usage-grid">
 ${card('فاکتور امروز',u.invoices_today||0,l.invoice_daily_limit,'فاکتور')}${card('مشتری',u.customers||0,l.customer_limit,'مشتری')}${card('پیامک ماهانه',u.sms_used||0,l.sms_credits,'اعتبار')}${card('اعتبار AI',u.ai_used||0,l.ai_credits,'اعتبار')}</div>
 <h3 class="sub-section-title">پلن‌های امپراتور</h3><div class="plans-grid">${plans.map(p=>planCard(p,s.plan_code)).join('')}</div>
 <h3 class="sub-section-title">تاریخچه اشتراک</h3><div class="sub-events">${events.map(e=>`<div class="sub-event"><span>${e.event_type==='renew'?'تمدید اشتراک':'ارتقای پلن'} · ${e.plan_name||''}</span><strong>${money(e.amount)}</strong></div>`).join('')||'<div class="sub-event">هنوز تراکنشی ثبت نشده است</div>'}</div>`;
 box.querySelectorAll('[data-plan]').forEach(b=>b.onclick=()=>upgrade(b.dataset.plan));
 }catch(e){box.innerHTML=`<div class="panel">${e.message||'خطا در دریافت اطلاعات اشتراک'}</div>`}
}
function card(title,used,limit,label){return `<div class="usage-card"><small>${title}</small><b>${Number(used).toLocaleString('fa-IR')} / ${Number(limit).toLocaleString('fa-IR')}</b><div class="meter"><i style="width:${pct(used,limit)}%"></i></div><small>${pct(used,limit)}٪ مصرف شده</small></div>`}
function planCard(p,current){const l=p.limits||{};return `<div class="plan-card ${p.code===current?'current':''}"><h3>${p.name}${p.code===current?' · فعلی':''}</h3><div class="price">${money(p.price_monthly)} <small>/ ماه</small></div><ul><li>${Number(l.invoice_daily_limit).toLocaleString('fa-IR')} فاکتور در روز</li><li>${Number(l.customer_limit).toLocaleString('fa-IR')} مشتری</li><li>${Number(l.sms_credits).toLocaleString('fa-IR')} اعتبار پیامک</li><li>${Number(l.ai_credits).toLocaleString('fa-IR')} اعتبار AI</li></ul>${p.code===current?'':'<button class="primary" data-plan="'+p.code+'">ارتقا به این پلن</button>'}</div>`}
async function upgrade(code){if(!confirm('پلن انتخابی فعال شود؟'))return;try{await api('/subscription/upgrade',{method:'POST',body:JSON.stringify({plan:code})});await loadSubscription();alert('پلن با موفقیت تغییر کرد')}catch(e){alert(e.message)}}
async function renewSubscription(){if(!confirm('اشتراک ۳۰ روز دیگر تمدید شود؟'))return;try{await api('/subscription/renew',{method:'POST'});await loadSubscription();alert('اشتراک با موفقیت تمدید شد')}catch(e){alert(e.message)}}
window.addEventListener('load',()=>{setTimeout(addSubscriptionNav,100);const oldShow=window.showPage;window.showPage=function(id){oldShow(id);if(id==='subscription')loadSubscription()};});
})();