// Emperator frontend entrypoint. Original application is preserved in app-core.js.
(function(){
  function load(src,next){
    const s=document.createElement('script');
    s.src=src;
    s.onload=next;
    s.onerror=function(){console.error('Emperator: failed to load '+src)};
    document.head.appendChild(s);
  }
  load('app-core.js',function(){
    load('auth-fix.js',function(){
      if(window.emperatorAuthFix)window.emperatorAuthFix.install();
    });
  });
})();
