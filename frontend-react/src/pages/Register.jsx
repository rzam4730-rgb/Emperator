import React, { useState } from 'react';
import { register } from '../services/api.js';

export default function Register() {
  const [form,setForm]=useState({phone:'',password:'',first_name:'',last_name:''});
  const [message,setMessage]=useState('');
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  const set=(key)=>(e)=>setForm({...form,[key]:e.target.value});
  async function submit(e){
    e.preventDefault(); setError(''); setMessage(''); setLoading(true);
    try { await register(form); setMessage('ثبت‌نام انجام شد. اکنون می‌توانید وارد شوید.'); }
    catch(err){ setError(err.message || 'ثبت‌نام انجام نشد.'); }
    finally{ setLoading(false); }
  }
  return <main className="auth-page" dir="rtl"><section className="auth-card">
    <div className="auth-brand"><span>♛</span><div><strong>امپراتور</strong><small>ایجاد حساب کسب‌وکار</small></div></div>
    <h1>ثبت‌نام</h1>
    <form onSubmit={submit}>
      <label>نام<input value={form.first_name} onChange={set('first_name')} /></label>
      <label>نام خانوادگی<input value={form.last_name} onChange={set('last_name')} /></label>
      <label>شماره موبایل<input dir="ltr" inputMode="tel" value={form.phone} onChange={set('phone')} placeholder="09123456789" /></label>
      <label>رمز عبور<input dir="ltr" type="password" value={form.password} onChange={set('password')} /></label>
      {error && <div className="auth-error">{error}</div>}{message && <div className="auth-success">{message}</div>}
      <button className="primary wide" disabled={loading}>{loading?'در حال ثبت‌نام...':'ایجاد حساب'}</button>
    </form>
  </section></main>;
}
