/* Emperator — Kitchen Display System module */
(function(){
  const statuses=[
    {key:'جدید',title:'🔵 جدید'},
    {key:'در حال آماده‌سازی',title:'🟡 در حال آماده‌سازی'},
    {key:'آماده',title:'🟢 آماده'}
  ];
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fa=n=>Number(n||0).toLocaleString('fa-IR');
  let timer=null;
  async function loadKDS(){
    const root=document.querySelector('#kitchen .kanban');
    if(!root||typeof api!=='function')return;
    try{
      const orders=await api('/kds/orders');
      root.innerHTML=statuses.map(s=>{
        const rows=orders.filter(o=>o.status===s.key);
        return `<div class="kanban-col"><h3>${s.title} <span>${fa(rows.length)}</span></h3>${rows.map(o=>`<article data-kds-id="${o.id}"><div style="display:flex;justify-content:space-between;gap:8px"><b>#${o.id}</b><small>${esc(o.customer_name||'مشتری حضوری')}</small></div>${(o.items||[]).map(i=>`<div style="margin-top:8px"><b>${fa(i.quantity)} × ${esc(i.name)}</b></div>`).join('')}<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:12px">${nextButtons(o.status,o.id)}</div></article>`).join('')||'<div class="empty-panel" style="padding:40px 10px">سفارشی در این مرحله نیست</div>'}</div>`;
      }).join('');
      root.querySelectorAll('[data-kds-next]').forEach(b=>b.onclick=()=>changeStatus(+b.dataset.id,b.dataset.kdsNext));
    }catch(e){root.innerHTML=`<div class="empty-panel">خطا در دریافت سفارش‌های آشپزخانه: ${esc(e.message)}</div>`}
  }
  function nextButtons(status,id){
    const map={'جدید':[['در حال آماده‌سازی','شروع آماده‌سازی'],['لغوشده','لغو']], 'در حال آماده‌سازی':[['آماده','اعلام آماده‌بودن'],['لغوشده','لغو']], 'آماده':[['تحویل‌شده','تحویل']]};
    return (map[status]||[]).map(x=>`<button class="table button" data-kds-next="${x[0]}" data-id="${id}" style="background:#25364b;color:#fff;border:0;border-radius:7px;padding:7px 10px">${x[1]}</button>`).join('');
  }
  async function changeStatus(id,status){
    try{await api('/orders/'+id+'/status',{method:'PATCH',body:JSON.stringify({status})});await loadKDS();}
    catch(e){alert(e.message||'تغییر وضعیت سفارش ناموفق بود')}
  }
  function init(){
    const page=document.getElementById('kitchen');
    if(!page)return;
    loadKDS();
    if(timer)clearInterval(timer);
    timer=setInterval(()=>{if(page.classList.contains('active'))loadKDS()},5000);
  }
  window.EmperatorKDS={load:loadKDS,init};
  document.addEventListener('DOMContentLoaded',init);
})();
