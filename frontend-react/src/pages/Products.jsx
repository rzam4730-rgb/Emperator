import React from 'react';

export default function Products(){
 return <div className="page">
  <div className="page-head"><div><h1>محصولات و منو</h1><p>مدیریت آیتم‌های منو، دسته‌بندی‌ها و قیمت‌ها</p></div><button className="primary">＋ محصول جدید</button></div>
  <div className="panel"><div className="panel-head"><h2>لیست محصولات</h2><button className="ghost-btn">فیلتر</button></div><div className="empty-state"><b>هنوز محصولی ثبت نشده است</b><span>محصولات منو پس از ثبت در این بخش نمایش داده می‌شوند.</span></div></div>
 </div>
}
