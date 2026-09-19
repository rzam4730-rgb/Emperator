import { useState } from 'react';
import type { FormEvent } from 'react';
import { getDashboard, register } from './api';
import type { DashboardData } from './api';

export default function App() {
  const [tokens, setTokens] = useState<string>('');
  const [data, setData] = useState<DashboardData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({ name: '', phone: '', password: '', restaurant_name: '' });

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setError('');
    try {
      const result = await register(form);
      setTokens(result.access_token);
      setData(await getDashboard(result.access_token));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'خطای نامشخص');
    } finally {
      setBusy(false);
    }
  }

  if (!tokens || !data) return <main className="auth-wrap"><form className="auth-card" onSubmit={submit}>
    <div className="brand-mark">ا</div><h1>امپراتور</h1><p>ساخت حساب مجموعه و دریافت داشبورد زنده</p>
    {([['name','نام مدیر'],['phone','شماره موبایل'],['password','رمز عبور (حداقل ۸ کاراکتر)'],['restaurant_name','نام مجموعه']] as const).map(([key,label]) => <label key={key}>{label}<input required minLength={key==='password'?8:undefined} type={key==='password'?'password':'text'} value={form[key]} onChange={e=>setForm({...form,[key]:e.target.value})}/></label>)}
    {error && <div className="error-box">{error}</div>}
    <button className="primary-button" disabled={busy}>{busy?'در حال اتصال…':'ثبت‌نام و دریافت داشبورد'}</button>
    <small>این مرحله از endpoint ثبت‌نام موجود استفاده می‌کند؛ ورود کاربران ثبت‌شده هنوز در این نمونه پیاده‌سازی نشده است.</small>
  </form></main>;

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark">ا</div><div><strong>امپراتور</strong><small>سامانه مدیریت کسب‌وکار</small></div></div><nav><button className="nav-link active">نمای کلی</button></nav></aside><main className="main-area"><header className="topbar"><b>داشبورد زنده</b><span>اطلاعات دریافتی از API</span></header><section className="content"><div className="page-heading"><div><div className="eyebrow">نمای کلی کسب‌وکار</div><h1>داشبورد مجموعه</h1><p>آمار دریافت‌شده از سرور</p></div><button className="primary-button" disabled={busy} onClick={async()=>{setBusy(true);setError('');try{setData(await getDashboard(tokens))}catch(e){setError(e instanceof Error?e.message:'خطا')}finally{setBusy(false)}}}>{busy?'در حال دریافت…':'به‌روزرسانی'}</button></div>{error&&<div className="error-box">{error}</div>}<div className="stats-grid">{[['تعداد سفارش‌ها',data.orders],['مجموع فروش',`${Number(data.sales).toLocaleString('fa-IR')} تومان`],['تعداد مشتریان',data.customers]].map(([label,value])=><article className="stat-card" key={String(label)}><div className="stat-top">{label}</div><div className="stat-value">{value}</div></article>)}</div><p className="muted">آمار بر اساس خروجی فعلی API است؛ بازهٔ زمانی فروش هنوز از سمت بک‌اند تفکیک نشده است.</p></section></main></div>;
}
