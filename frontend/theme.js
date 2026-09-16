/* Emperator — fixed top navigation + reliable light/dark theme */
(function(){
  const LIGHT_STYLE = `
    :root[data-theme="light"]{--bg:#eef5f2;--bg2:#ffffff;--panel:#ffffff;--panel2:#f4faf7;--line:#d5e2dc;--text:#17231f;--muted:#5f7069;--gold:#b97808;--gold2:#9b6100;--green:#11865a;--blue:#2278bd;--red:#c83e4c}
    :root[data-theme="light"] body{background:linear-gradient(135deg,#f8fbfa 0%,#e8f1ed 100%);color:var(--text)}
    :root[data-theme="light"] .topbar{background:rgba(255,255,255,.97);box-shadow:0 2px 18px rgba(35,65,55,.08)}
    :root[data-theme="light"] .nav:hover,:root[data-theme="light"] .nav.active{background:#e5f0eb;color:#8a5600;box-shadow:inset 0 -2px 0 #c58a25}
    :root[data-theme="light"] .stat-card,:root[data-theme="light"] .panel{background:linear-gradient(145deg,#ffffff,#f5faf8);border-color:#d5e2dc;box-shadow:0 5px 18px rgba(31,67,55,.06)}
    :root[data-theme="light"] .stat-icon{background:#e4f0eb}
    :root[data-theme="light"] .product,:root[data-theme="light"] .quick button,:root[data-theme="light"] .report-grid button,:root[data-theme="light"] .pay-grid button,:root[data-theme="light"] .kanban-col article{background:linear-gradient(145deg,#ffffff,#f1f7f4);border-color:#d5e2dc}
    :root[data-theme="light"] .kanban-col{background:#e7f0ec;border-color:#cfded7}
    :root[data-theme="light"] .kds-action{box-shadow:0 2px 7px rgba(25,60,48,.08)}
    :root[data-theme="light"] .table button{background:#e1ece8;color:#203c32}
    :root[data-theme="light"] .theme-toggle{background:#fff8e9;border-color:#e0c37c;color:#8a5600}
  `;
  function installLightStyle(){
    if(document.getElementById('emperator-light-theme'))return;
    const s=document.createElement('style');s.id='emperator-light-theme';s.textContent=LIGHT_STYLE;document.head.appendChild(s);
  }
  function applyTheme(mode){
    mode=mode==='light'?'light':'dark';
    document.documentElement.setAttribute('data-theme',mode);
    if(document.body)document.body.setAttribute('data-theme',mode);
    try{localStorage.setItem('emperator_theme',mode)}catch(e){}
    const b=document.getElementById('themeToggle');
    if(b){b.textContent=mode==='dark'?'☀':'☾';b.title=mode==='dark'?'حالت روز':'حالت شب';b.setAttribute('aria-label',b.title)}
  }
  function init(){
    installLightStyle();
    const main=document.querySelector('.main-nav'),more=document.getElementById('moreMenu');
    if(main&&more){more.querySelectorAll('.nav[data-page]').forEach(btn=>main.appendChild(btn));more.remove();const moreBtn=document.getElementById('moreBtn');if(moreBtn)moreBtn.remove()}
    document.querySelectorAll('.main-nav .nav[data-page]').forEach(btn=>{btn.onclick=function(e){e.preventDefault();if(typeof window.emperatorNavigate==='function')window.emperatorNavigate(btn.getAttribute('data-page'));else if(typeof window.showPage==='function')window.showPage(btn.getAttribute('data-page'))}});
    const userbar=document.querySelector('.userbar');
    if(userbar){let b=document.getElementById('themeToggle');if(!b){b=document.createElement('button');b.id='themeToggle';b.className='iconbtn theme-toggle';b.type='button';userbar.insertBefore(b,userbar.firstChild||null)}b.onclick=function(e){e.preventDefault();e.stopPropagation();applyTheme((document.documentElement.getAttribute('data-theme')||'dark')==='dark'?'light':'dark')}}
    let saved='dark';try{saved=localStorage.getItem('emperator_theme')||'dark'}catch(e){}applyTheme(saved);
    if(window.EmperatorKDS&&typeof window.EmperatorKDS.init==='function')window.EmperatorKDS.init();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
