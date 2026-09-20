import React from 'react';

export default function Topbar({title,name='مدیر',initial='م'}){
 return <header className="topbar">
  <div className="topbar-right">
   <button className="icon-btn sidebar-toggle">☰</button>
   <div className="breadcrumb"><span>امپراتور</span><b>/</b><strong>{title}</strong></div>
  </div>
  <div className="topbar-left">
   <button className="icon-btn">♢</button>
   <button className="help-btn">؟ راهنما</button>
   <div className="profile"><div className="avatar">{initial}</div><div className="profile-copy"><b>{name}</b><small>مدیر مجموعه</small></div></div>
  </div>
 </header>
}
