import React from 'react';

export default function Inventory(){
 return <div className="page">
  <div className="page-head"><div><h1>موجودی و انبار</h1><p>کنترل مواد اولیه، کالاها و هشدار کمبود موجودی</p></div><button className="primary">＋ ورود کالا</button></div>
  <div className="stats"><div className="stat-card"><span>موجودی کل</span><b>—</b></div><div className="stat-card"><span>هشدار کمبود</span><b>—</b></div></div>
  <div className="panel"><h2>لیست انبار</h2><div className="empty-state">اطلاعات انبار پس از اتصال API نمایش داده می‌شود.</div></div>
 </div>
}
