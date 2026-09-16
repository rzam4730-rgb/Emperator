/* Emperator emergency navigation: independent of other modules. */
(function(){
  function show(id){
    var page=document.getElementById(id);
    if(!page)return false;
    document.querySelectorAll('.page').forEach(function(p){p.classList.toggle('active',p.id===id)});
    document.querySelectorAll('.nav[data-page]').forEach(function(n){n.classList.toggle('active',n.getAttribute('data-page')===id)});
    var menu=document.getElementById('moreMenu');
    if(menu)menu.classList.remove('show');
    window.scrollTo(0,0);
    return true;
  }
  function wire(){
    var more=document.getElementById('moreBtn');
    if(more && !more.dataset.emergencyNav){
      more.dataset.emergencyNav='1';
      more.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();var m=document.getElementById('moreMenu');if(m)m.classList.toggle('show')},true);
    }
    document.querySelectorAll('.nav[data-page]').forEach(function(btn){
      if(btn.dataset.emergencyNav)return;
      btn.dataset.emergencyNav='1';
      btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.getAttribute('data-page'))},true);
    });
    document.querySelectorAll('[data-go]').forEach(function(btn){
      if(btn.dataset.emergencyGo)return;
      btn.dataset.emergencyGo='1';
      btn.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();show(btn.getAttribute('data-go'))},true);
    });
    var checkout=document.getElementById('checkoutBtn');
    if(checkout && !checkout.dataset.emergencyCheckout){
      checkout.dataset.emergencyCheckout='1';
      checkout.addEventListener('click',function(e){e.preventDefault();e.stopImmediatePropagation();if(typeof window.checkout==='function')window.checkout();},true);
    }
    window.emperatorNavigate=show;
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',wire,{once:true});else wire();
  setTimeout(wire,300);setTimeout(wire,1000);
})();
