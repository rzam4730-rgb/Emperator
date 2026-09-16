/* Emperator — top navigation + light/dark theme */
(function(){
  function applyTheme(mode){
    document.documentElement.dataset.theme=mode;
    localStorage.setItem('emperator_theme',mode);
    const b=document.getElementById('themeToggle');
    if(b) b.textContent=mode==='dark'?'☀':'☾';
    if(b) b.title=mode==='dark'?'حالت روز':'حالت شب';
  }
  function init(){
    const main=document.querySelector('.main-nav');
    const more=document.getElementById('moreMenu');
    if(main&&more){
      more.querySelectorAll('.nav[data-page]').forEach(function(btn){
        main.appendChild(btn);
      });
      more.remove();
      const moreBtn=document.getElementById('moreBtn');
      if(moreBtn) moreBtn.remove();
    }
    const userbar=document.querySelector('.userbar');
    if(userbar){
      let b=document.getElementById('themeToggle');
      if(!b){
        b=document.createElement('button');
        b.id='themeToggle'; b.className='iconbtn'; b.type='button';
        userbar.insertBefore(b,userbar.firstChild||null);
      }
      b.onclick=function(){applyTheme((document.documentElement.dataset.theme||'dark')==='dark'?'light':'dark')};
    }
    applyTheme(localStorage.getItem('emperator_theme')||'dark');
    if(window.EmperatorKDS&&typeof window.EmperatorKDS.init==='function') window.EmperatorKDS.init();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true}); else init();
})();
