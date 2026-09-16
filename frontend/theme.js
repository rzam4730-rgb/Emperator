/* Emperator theme */
(function(){
const LIGHT_STYLE=`
:root[data-theme="light"]{--bg:#eef4f1;--bg2:#fff;--panel:#fff;--panel2:#f6faf8;--line:#d6e2dd;--text:#17231f;--muted:#63736c;--gold:#b97908;--gold2:#925b00;--green:#11865a;--blue:#287fbe;--red:#c84652}
:root[data-theme="light"] body{background:radial-gradient(circle at 88% 8%,rgba(213,177,92,.14),transparent 28%),radial-gradient(circle at 12% 18%,rgba(34,126,98,.1),transparent 25%),linear-gradient(135deg,#f9fcfb,#edf4f1 55%,#e7f0ec);color:var(--text)}
:root[data-theme="light"] .topbar{background:rgba(255,255,255,.94);backdrop-filter:blur(12px);box-shadow:0 4px 24px rgba(28,62,51,.08);border-bottom:1px solid #d2e0da}
:root[data-theme="light"] .main-nav{background:rgba(255,255,255,.72);border:1px solid #dce8e3;box-shadow:0 3px 14px rgba(32,69,57,.05)}
:root[data-theme="light"] .nav{color:#52645d;border-color:transparent}
:root[data-theme="light"] .nav:hover{background:#eef7f3;color:#8a5600}
:root[data-theme="light"] .nav.active{background:linear-gradient(135deg,#e6f3ee,#f8f3e7);color:#8a5600;box-shadow:inset 0 -2px #c58a25,0 2px 8px rgba(31,67,55,.06)}
:root[data-theme="light"] .page-head{background:linear-gradient(90deg,rgba(255,255,255,.85),rgba(248,252,250,.55));border-color:#dce7e2;border-radius:18px;padding:16px 18px;box-shadow:0 4px 18px rgba(35,65,55,.05)}
:root[data-theme="light"] .stat-card,:root[data-theme="light"] .panel{background:linear-gradient(145deg,#fff,#f7fbf9);border-color:#d6e2dd;box-shadow:0 7px 22px rgba(31,67,55,.07);transition:.18s}
:root[data-theme="light"] .stat-card:hover,:root[data-theme="light"] .panel:hover{transform:translateY(-2px);box-shadow:0 11px 28px rgba(31,67,55,.1)}
:root[data-theme="light"] .stat-icon{background:linear-gradient(135deg,#e0f0e9,#fff4dc);border:1px solid #d7e5df}
:root[data-theme="light"] .product,:root[data-theme="light"] .quick button,:root[data-theme="light"] .report-grid button,:root[data-theme="light"] .pay-grid button,:root[data-theme="light"] .kanban-col article{background:linear-gradient(145deg,#fff,#f1f7f4);border-color:#d6e2dd;box-shadow:0 4px 14px rgba(31,67,55,.055);transition:.16s}
:root[data-theme="light"] .product:hover,:root[data-theme="light"] .quick button:hover,:root[data-theme="light"] .report-grid button:hover,:root[data-theme="light"] .pay-grid button:hover,:root[data-theme="light"] .kanban-col article:hover{transform:translateY(-2px);border-color:#c7d9d1;box-shadow:0 9px 20px rgba(31,67,55,.09)}
:root[data-theme="light"] .kanban-col{background:linear-gradient(180deg,#edf5f2,#e6efeb);border-color:#cfddd7}
:root[data-theme="light"] .table{background:#fff;border-color:#d6e2dd;box-shadow:0 5px 18px rgba(31,67,55,.055)}
:root[data-theme="light"] .table th{background:#eef6f2;color:#49615a}.table td{border-color:#e4ece8}
:root[data-theme="light"] .table tr:hover td{background:#f8fbfa}
:root[data-theme="light"] input,:root[data-theme="light"] select,:root[data-theme="light"] textarea{background:#fff;border-color:#ccdcd5;color:#1b2924}
:root[data-theme="light"] input:focus,:root[data-theme="light"] select:focus,:root[data-theme="light"] textarea:focus{border-color:#b97908;box-shadow:0 0 0 3px rgba(185,121,8,.12)}
:root[data-theme="light"] .primary{box-shadow:0 5px 14px rgba(185,121,8,.2)}
:root[data-theme="light"] .theme-toggle{background:linear-gradient(135deg,#fff7df,#eef7f3);border-color:#dfc67f;color:#8a5600;box-shadow:0 3px 10px rgba(55,75,65,.08)}
`;
function installLightStyle(){const old=document.getElementById('emperator-light-theme');if(old)old.remove();const s=document.createElement('style');s.id='emperator-light-theme';s.textContent=LIGHT_STYLE;document.head.appendChild(s)}
function applyTheme(mode){mode=mode==='light'?'light':'dark';document.documentElement.setAttribute('data-theme',mode);if(document.body)document.body.setAttribute('data-theme',mode);try{localStorage.setItem('emperator_theme',mode)}catch(e){}const b=document.getElementById('themeToggle');if(b){b.textContent=mode==='dark'?'☀':'☾';b.title=mode==='dark'?'حالت روز':'حالت شب';b.setAttribute('aria-label',b.title)}}
function init(){installLightStyle();const main=document.querySelector('.main-nav'),more=document.getElementById('moreMenu');if(main&&more){more.querySelectorAll('.nav[data-page]').forEach(btn=>main.appendChild(btn));more.remove();const moreBtn=document.getElementById('moreBtn');if(moreBtn)moreBtn.remove()}document.querySelectorAll('.main-nav .nav[data-page]').forEach(btn=>{btn.onclick=function(e){e.preventDefault();if(typeof window.emperatorNavigate==='function')window.emperatorNavigate(btn.getAttribute('data-page'));else if(typeof window.showPage==='function')window.showPage(btn.getAttribute('data-page'))}});const userbar=document.querySelector('.userbar');if(userbar){let b=document.getElementById('themeToggle');if(!b){b=document.createElement('button');b.id='themeToggle';b.className='iconbtn theme-toggle';b.type='button';userbar.insertBefore(b,userbar.firstChild||null)}b.onclick=function(e){e.preventDefault();e.stopPropagation();applyTheme((document.documentElement.getAttribute('data-theme')||'dark')==='dark'?'light':'dark')}}let saved='dark';try{saved=localStorage.getItem('emperator_theme')||'dark'}catch(e){}applyTheme(saved);if(window.EmperatorKDS&&typeof window.EmperatorKDS.init==='function')window.EmperatorKDS.init()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();})();
