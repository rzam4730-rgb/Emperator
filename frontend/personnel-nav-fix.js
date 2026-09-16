/* Emperator: expose Personnel directly in the main navigation. */
(function(){
  function movePersonnel(){
    var item=document.querySelector('.more-menu .nav[data-page="personnel"]');
    var nav=document.querySelector('.main-nav');
    if(!item||!nav||nav.querySelector('[data-page="personnel"]'))return;
    var clone=item.cloneNode(true);
    clone.classList.remove('active');
    nav.insertBefore(clone,document.getElementById('moreBtn'));
    clone.addEventListener('click',function(e){
      e.preventDefault();
      e.stopImmediatePropagation();
      if(typeof window.showPage==='function')window.showPage('personnel');
      else if(typeof window.emperatorNavigate==='function')window.emperatorNavigate('personnel');
    },true);
  }
  function boot(){movePersonnel();setTimeout(movePersonnel,300);setTimeout(movePersonnel,1000);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();