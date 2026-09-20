import React, { useState } from 'react';
import { useAuth } from '../auth/AuthProvider.jsx';

export default function Login() {
  const { signIn } = useAuth();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setError('');
    if (!phone.trim() || !password) {
      setError('شماره موبایل و رمز عبور را وارد کنید.');
      return;
    }
    setLoading(true);
    try {
      await signIn(phone.trim(), password);
    } catch (err) {
      setError(err.message || 'ورود انجام نشد.');
    } finally {
      setLoading(false);
    }
  }

  return <main className="auth-page" dir="rtl">
    <section className="auth-card">
      <div className="auth-brand"><span>♛</span><div><strong>امپراتور</strong><small>مدیریت هوشمند کسب‌وکار غذایی</small></div></div>
      <h1>ورود به حساب</h1>
      <p className="muted">برای ورود، شماره موبایل و رمز عبور خود را وارد کنید.</p>
      <form onSubmit={submit}>
        <label>شماره موبایل<input dir="ltr" inputMode="tel" autoComplete="tel" value={phone} onChange={e=>setPhone(e.target.value)} placeholder="09123456789" /></label>
        <label>رمز عبور<input dir="ltr" type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" /></label>
        {error && <div className="auth-error">{error}</div>}
        <button className="primary wide" disabled={loading}>{loading ? 'در حال ورود...' : 'ورود به امپراتور'}</button>
      </form>
      <div className="auth-note">حساب قبلی شما حفظ شده است؛ نیازی به ثبت‌نام مجدد نیست.</div>
    </section>
  </main>;
}
