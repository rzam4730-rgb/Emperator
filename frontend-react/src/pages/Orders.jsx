import React from 'react';

export default function Orders(){
 return <div className="page-module">
  <div className="page-head"><div><span className="eyebrow">مدیریت فروش</span><h1>سفارش‌ها</h1><p>مدیریت سفارش‌های ثبت شده و وضعیت آماده‌سازی.</p></div><button className="primary">＋ سفارش جدید</button></div>
  <section className="panel"><div className="panel-head"><h2>لیست سفارش‌ها</h2><button className="ghost-btn">فیلتر</button></div>
  <div className="empty-state"><div className="empty-icon">▣</div><b>هنوز سفارشی ثبت نشده است</b><span>پس از ثبت سفارش‌ها، اطلاعات مشتری، مبلغ و وضعیت نمایش داده می‌شود.</span></div></section>
 </div>
}
