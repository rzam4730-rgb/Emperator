/* Emperator — fixed top navigation + reliable light/dark theme */
(function(){
  function applyTheme(mode){
    mode = mode === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', mode);
    document.body && document.body.setAttribute('data-theme', mode);
    try{ localStorage.setItem('emperator_theme', mode); }catch(e){}
    const b=document.getElementById('themeToggle');
    if(b){
      b.textContent = mode === 'dark' ? '☀' : '☾';
      b.title = mode === 'dark' ? 'حالت روز' : 'حالت شب';
      b.setAttribute('aria-label', b.title);
    }
  }
  function init(){
    const main=document.querySelector('.main-nav');
    const more=document.getElementById('moreMenu');
    if(main && more){
      more.querySelectorAll('.nav[data-page]').forEach(function(btn){ main.appendChild(btn); });
      more.remove();
      const moreBtn=document.getElementById('moreBtn');
      if(moreBtn) moreBtn.remove();
    }

    const userbar=document.querySelector('.userbar');
    if(userbar){
      let b=document.getElementById('themeToggle');
      if(!b){
        b=document.createElement('button');
        b.id='themeToggle';
        b.className='iconbtn theme-toggle';
        b.type='button';
        userbar.insertBefore(b,userbar.firstChild||null);
      }
      b.onclick=function(e){
        e.preventDefault();
        e.stopPropagation();
        const current=document.documentElement.getAttribute('data-theme') || 'dark';
        applyTheme(current === 'dark' ? 'light' : 'dark');
      };
    }

    let saved='dark';
    try{ saved=localStorage.getItem('emperator_theme') || 'dark'; }catch(e){}
    applyTheme(saved);

    if(window.EmperatorKDS && typeof window.EmperatorKDS.init==='function') window.EmperatorKDS.init();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',init,{once:true});
  else init();
})();
