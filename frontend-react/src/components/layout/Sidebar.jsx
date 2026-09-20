import React from 'react';

const items=[
 ['⌂','داشبورد'],['▣','سفارش‌ها'],['◉','مشتریان'],['▤','محصولات و منو'],
 ['▥','موجودی و انبار'],['◫','خرید و تأمین'],['▦','گزارش‌ها'],
 ['◌','باشگاه مشتریان'],['◈','پیامک و ارتباطات'],['⚙','تنظیمات']
];

export default function Sidebar({active,onChange,collapsed,signOut}){
 return <aside className={`sidebar ${collapsed?'collapsed':''}`}>
  <div className="sidebar-brand"><div className="brand-mark">♛</div><div className="brand-copy"><b>امپراتور</b><small>مدیریت کسب‌وکار غذایی</small></div></div>
  <nav className="sidebar-nav">
   <span className="nav-title">مدیریت</span>
   {items.map(([icon,label])=><button key={label} onClick={()=>onChange(label)} className={active===label?'nav-item active':'nav-item'}><span className="nav-icon">{icon}</span><span className="nav-label">{label}</span></button>)}
  </nav>
  <button className="nav-item logout-item" onClick={signOut}><span className="nav-icon">⇥</span><span className="nav-label">خروج</span></button>
 </aside>
}
