import React from 'react';

export default function Customers(){
 return <div className="page-module">
  <div className="page-head"><div><span className="eyebrow">باشگاه مشتریان</span><h1>مشتریان</h1><p>مدیریت اطلاعات مشتریان و تاریخچه خرید.</p></div><button className="primary">＋ مشتری جدید</button></div>
  <section className="panel"><div className="panel-head"><h2>لیست مشتریان</h2><button className="ghost-btn">جستجو</button></div>
  <div className="empty-state"><div className="empty-icon">◉</div><b>مشتری ثبت نشده است</b><span>اطلاعات مشتریان پس از اتصال API نمایش داده خواهد شد.</span></div></section>
 </div>
}
