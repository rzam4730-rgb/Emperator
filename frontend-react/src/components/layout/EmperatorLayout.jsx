import React from 'react';

/**
 * Shared application shell for Emperator modules.
 * Keeps Sidebar/Topbar structure independent from business pages.
 */
export default function EmperatorLayout({children, sidebar, topbar}) {
  return (
    <div className="emperator-shell" dir="rtl">
      <aside className="emperator-sidebar">{sidebar}</aside>
      <section className="emperator-main">
        <header className="emperator-topbar">{topbar}</header>
        <main className="emperator-content">{children}</main>
      </section>
    </div>
  );
}
