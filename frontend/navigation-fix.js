// Emperator navigation fix: works even when app-core.js fails to initialize.
(function(){
  function show(id){
    document.querySelectorAll('.page').forEach(function(p){p.classList.toggle('active',p.id===id)});
    document.querySelectorAll('.nav[data-page]').forEach(function(n){n.classList.toggle('active',n.getAttribute('data-page')===id)});
    var menu=document.getElementById('moreMenu'); if(menu) menu.classList.remove('show');
    window.scrollTo(0,0);
    if(typeof window.showPage==='function' && window.showPage!==show){try{window.showPage(id)}catch(_){}
    }
  }
  function wire(){
    document.querySelectorAll('.nav[data-page]').forEach(function(btn){btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.getAttribute('data-page'))},true)});
    document.querySelectorAll('[data-go]').forEach(function(btn){btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.getAttribute('data-go'))},true)});
    var dash=document.querySelector('#dashboard .page-head .primary'); if(dash) dash.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show('pos')},true);
    var orders=document.querySelector('#orders .page-head .primary'); if(orders) orders.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show('pos')},true);
    window.emperatorNavigate=show;
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire,{once:true}); else wire();
})();
