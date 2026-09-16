// Emperator navigation fix.
(function(){
  function wire(){
    if(typeof window.showPage!=='function') return;
    document.querySelectorAll('.nav[data-page]').forEach(function(btn){
      btn.onclick=function(e){e.preventDefault();e.stopPropagation();window.showPage(btn.dataset.page)};
    });
    document.querySelectorAll('[data-go]').forEach(function(btn){
      btn.onclick=function(e){e.preventDefault();e.stopPropagation();window.showPage(btn.dataset.go)};
    });
    document.querySelectorAll('#dashboard .page-head .primary,#orders .page-head .primary').forEach(function(btn){
      btn.onclick=function(e){e.preventDefault();window.showPage('pos')};
    });
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',wire,{once:true});
  else wire();
})();
