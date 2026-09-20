import React from 'react';
import Sidebar from './Sidebar.jsx';
import Topbar from './Topbar.jsx';

export default function MainLayout({children, active='داشبورد'}) {
  return (
    <div className="app-shell dashboard-shell" dir="rtl">
      <Sidebar active={active} />
      <section className="main-area">
        <Topbar active={active} />
        <main className="content">{children}</main>
      </section>
    </div>
  );
}
