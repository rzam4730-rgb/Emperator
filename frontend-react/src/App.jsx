import React,{useState} from 'react';
import {AuthProvider,useAuth} from './auth/AuthProvider.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';

const navItems=[
  ['⌂','داشبورد'],
  ['▣','سفارش‌ها'],
  ['◉','مشتریان'],
  ['▤','محصولات و منو'],
  ['▥','موجودی و انبار'],
  ['◫','خرید و تأمین'],
  ['▦','گزارش‌ها'],
  ['◌','باشگاه مشتریان'],
  ['◈','پیامک و ارتباطات'],
  ['⚙','تنظیمات']
];

function Dashboard(){
  const{user,signOut}=useAuth();
  const[active,setActive]=useState('داشبورد');
  const[collapsed,setCollapsed]=useState(false);
  const name=user?.first_name?(user.first_name+' '+(user.last_name||'')):(user?.phone||'کاربر');
  const initial=(user?.first_name||name||'ک').trim().charAt(0);

  return <div className={`app-shell dashboard-shell ${collapsed?'sidebar-collapsed':''}`} dir="rtl">
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">♛</div>
        <div className="brand-copy"><b>امپراتور</b><small>مدیریت کسب‌وکار غذایی</small></div>
      </div>

      <div className="workspace">
        <span className="workspace-dot"></span>
        <div><small>کسب‌وکار فعال</small><b>مجموعه امپراتور</b></div>
        <span className="workspace-chevron">⌄</span>
      </div>

      <nav className="sidebar-nav">
        <span className="nav-title">مدیریت</span>
        {navItems.map(([icon,label])=><button key={label} className={active===label?'nav-item active':'nav-item'} onClick={()=>setActive(label)} title={label}>
          <span className="nav-icon">{icon}</span><span className="nav-label">{label}</span>
        </button>)}
      </nav>

      <div className="sidebar-bottom">
        <div className="support-card"><span>✦</span><div><b>دستیار امپراتور</b><small>آماده کمک به شماست</small></div></div>
        <button className="nav-item logout-item" onClick={signOut}><span className="nav-icon">⇥</span><span className="nav-label">خروج از حساب</span></button>
      </div>
    </aside>

    <section className="main-area">
      <header className="topbar">
        <div className="topbar-right">
          <button className="icon-btn sidebar-toggle" onClick={()=>setCollapsed(v=>!v)} aria-label="نمایش یا مخفی کردن منو">☰</button>
          <div className="breadcrumb"><span>امپراتور</span><b>/</b><strong>{active}</strong></div>
        </div>
        <div className="topbar-left">
          <button className="icon-btn" title="اعلان‌ها">♢<i></i></button>
          <button className="help-btn">؟ راهنما</button>
          <div className="profile">
            <div className="avatar">{initial}</div>
            <div className="profile-copy"><b>{name}</b><small>مدیر مجموعه</small></div>
            <span className="chevron">⌄</span>
          </div>
        </div>
      </header>

      <main className="content">
        <div className="page-head">
          <div><span className="eyebrow">نمای کلی کسب‌وکار</span><h1>سلام، {user?.first_name||'مدیر'} 👋</h1><p>وضعیت امروز مجموعه‌تان را در یک نگاه بررسی کنید.</p></div>
          <button className="primary">＋ ثبت سفارش جدید</button>
        </div>

        <div className="stats">
          <div className="stat-card"><div className="stat-top"><span>فروش امروز</span><span className="stat-icon gold">﷼</span></div><b>—</b><small>در انتظار اطلاعات فروش</small></div>
          <div className="stat-card"><div className="stat-top"><span>سفارش‌های امروز</span><span className="stat-icon blue">▣</span></div><b>—</b><small>تعداد سفارش‌های ثبت‌شده</small></div>
          <div className="stat-card"><div className="stat-top"><span>مشتریان فعال</span><span className="stat-icon green">◉</span></div><b>—</b><small>مشتریان ثبت‌شده</small></div>
          <div className="stat-card"><div className="stat-top"><span>هشدار موجودی</span><span className="stat-icon red">!</span></div><b>—</b><small>نیازمند بررسی</small></div>
        </div>

        <div className="dashboard-grid">
          <section className="panel sales-panel"><div className="panel-head"><div><h2>فروش و سفارش‌ها</h2><small>روند فعالیت ۷ روز اخیر</small></div><button className="ghost-btn">مشاهده گزارش</button></div><div className="chart-empty"><div className="chart-line"></div><span>پس از ثبت سفارش‌ها، نمودار عملکرد اینجا نمایش داده می‌شود.</span></div></section>
          <section className="panel quick-panel"><div className="panel-head"><div><h2>دسترسی سریع</h2><small>کارهای پرتکرار</small></div></div><div className="quick-actions"><button><span>＋</span><b>سفارش جدید</b><small>ثبت سفارش مشتری</small></button><button><span>♙</span><b>مشتری جدید</b><small>افزودن مشتری</small></button><button><span>▤</span><b>محصول جدید</b><small>افزودن به منو</small></button><button><span>▥</span><b>ثبت خرید</b><small>ورود کالا به انبار</small></button></div></section>
        </div>

        <section className="panel activity-panel"><div className="panel-head"><div><h2>آخرین سفارش‌ها</h2><small>آخرین فعالیت‌های ثبت‌شده</small></div><button className="ghost-btn">همه سفارش‌ها</button></div><div className="empty-state"><div className="empty-icon">◫</div><b>هنوز سفارشی ثبت نشده است</b><span>اولین سفارش را ثبت کنید تا فعالیت‌های مجموعه در این بخش نمایش داده شود.</span><button className="primary small">ثبت اولین سفارش</button></div></section>
      </main>
    </section>
  </div>
}

function Root(){
  const[registerMode,setRegisterMode]=useState(false);
  const{isAuthenticated}=useAuth();
  if(isAuthenticated)return <Dashboard/>;
  return registerMode?<><Register/><button className="auth-switch" onClick={()=>setRegisterMode(false)}>ورود به حساب</button></>:<><Login/><button className="auth-switch" onClick={()=>setRegisterMode(true)}>حساب ندارید؟ ثبت‌نام کنید</button></>
}

export default function App(){return <AuthProvider><Root/></AuthProvider>}
