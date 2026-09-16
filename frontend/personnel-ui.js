/* Emperator personnel module: makes personnel management a first-class navigation item. */
(function(){
  function show(id){
    document.querySelectorAll('.page').forEach(function(p){p.classList.toggle('active',p.id===id)});
    document.querySelectorAll('.nav[data-page]').forEach(function(n){n.classList.toggle('active',n.getAttribute('data-page')===id)});
    var menu=document.getElementById('moreMenu');if(menu)menu.classList.remove('show');
    window.scrollTo(0,0);
    if(typeof window.showPage==='function' && window.showPage!==show){try{window.showPage(id)}catch(_) {}}
  }
  function ensurePage(){
    if(document.getElementById('personnel'))return;
    var main=document.querySelector('main.content');if(!main)return;
    var section=document.createElement('section');section.className='page';section.id='personnel';
    section.innerHTML='<div class="page-head"><div><h1>امور پرسنلی</h1><p>مدیریت کارکنان، نقش‌ها، شیفت‌ها، حضور و غیاب و حقوق</p></div><button class="primary">＋ افزودن پرسنل</button></div><div class="stats mini"><div class="stat-card"><div><small>کل پرسنل</small><b>۱۸</b></div></div><div class="stat-card"><div><small>حاضر امروز</small><b>۱۵</b></div></div><div class="stat-card warn"><div><small>مرخصی امروز</small><b>۳</b></div></div></div><div class="panel"><div class="panel-title"><h3>مدیریت پرسنل</h3><span>پرونده، شیفت و عملکرد</span></div><div class="order"><span>👨‍🍳 علی محمدی</span><span>آشپز</span><b class="done">حاضر</b><strong>شیفت صبح</strong></div><div class="order"><span>🧑‍💼 سارا احمدی</span><span>صندوقدار</span><b class="done">حاضر</b><strong>شیفت صبح</strong></div><div class="order"><span>👨‍🍳 مهدی کریمی</span><span>آشپز</span><b class="cooking">مرخصی</b><strong>شیفت عصر</strong></div><div class="order"><span>👩‍💼 نرگس رضایی</span><span>مدیر شیفت</span><b class="done">حاضر</b><strong>شیفت عصر</strong></div></div>';
    main.appendChild(section);
  }
  function ensureNav(){
    var nav=document.querySelector('.main-nav');if(!nav||document.querySelector('.main-nav [data-page="personnel"]'))return;
    var more=document.getElementById('moreBtn');
    var btn=document.createElement('button');btn.className='nav';btn.setAttribute('data-page','personnel');btn.textContent='🧑‍💼 امور پرسنلی';
    btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show('personnel')},true);
    if(more)nav.insertBefore(btn,more);else nav.appendChild(btn);
  }
  function boot(){ensurePage();ensureNav();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  setTimeout(boot,300);setTimeout(boot,1200);
})();
