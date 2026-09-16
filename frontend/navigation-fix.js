// Emperator navigation fix.
(function(){
  function go(id){
    if(typeof window.showPage==='function') window.showPage(id);
  }
  function wire(){
    document.querySelectorAll('.nav[data-page]').forEach(function(btn){
      btn.addEventListener('click',function(e){
        e.preventDefault();
        e.stopPropagation();
        go(btn.getAttribute('data-page'));
      },true);
    });
    document.querySelectorAll('[data-go]').forEach(function(btn){
      btn.addEventListener('click',function(e){
        e.preventDefault();
        e.stopPropagation();
        go(btn.getAttribute('data-go'));
      },true);
    });
    var dash=document.querySelector('#dashboard .page-head .primary');
    if(dash) dash.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();go('pos')},true);
    var orders=document.querySelector('#orders .page-head .primary');
    if(orders) orders.addEventListener('click',function(e){e.preventDefault();e.stopPropagation();go('pos')},true);
  }
  function init(){ wire(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
