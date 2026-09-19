import { useState } from 'react';
import { LayoutDashboard, ShoppingCart, ChefHat, Package, Users, ChartNoAxesCombined, Settings, Search, Bell, Plus, ArrowUpLeft } from 'lucide-react';

type NavItem = { label: string; icon: typeof LayoutDashboard };
const nav: NavItem[] = [
  { label: 'داشبورد', icon: LayoutDashboard },
  { label: 'سفارش‌ها', icon: ShoppingCart },
  { label: 'آشپزخانه', icon: ChefHat },
  { label: 'انبار', icon: Package },
  { label: 'مشتریان', icon: Users },
  { label: 'گزارش‌ها', icon: ChartNoAxesCombined },
  { label: 'تنظیمات', icon: Settings },
];
const stats = [
  { label: 'فروش امروز', value: '۲۴,۸۵۰,۰۰۰', unit: 'تومان', change: '+۱۲٪' },
  { label: 'سفارش‌های امروز', value: '۱۲۸', unit: 'سفارش', change: '+۸٪' },
  { label: 'میانگین هر سفارش', value: '۱۹۴,۱۴۰', unit: 'تومان', change: '+۴٪' },
  { label: 'در انتظار آماده‌سازی', value: '۱۷', unit: 'سفارش', change: 'نیازمند بررسی' },
];
const orders = [
  { id: '#۱۰۴۸', customer: 'علی رضایی', type: 'ارسال با پیک', total: '۸۹۰,۰۰۰', status: 'در حال آماده‌سازی' },
  { id: '#۱۰۴۷', customer: 'مریم احمدی', type: 'تحویل حضوری', total: '۵۴۰,۰۰۰', status: 'ثبت‌شده' },
  { id: '#۱۰۴۶', customer: 'رضا محمدی', type: 'ارسال با پیک', total: '۱,۲۴۰,۰۰۰', status: 'آماده تحویل' },
  { id: '#۱۰۴۵', customer: 'سارا کریمی', type: 'تحویل حضوری', total: '۳۶۰,۰۰۰', status: 'تکمیل‌شده' },
];

export default function App() {
  const [active, setActive] = useState('داشبورد');
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark">ا</div><div><strong>امپراتور</strong><small>سامانه مدیریت کسب‌وکار</small></div></div>
      <div className="restaurant"><span className="restaurant-dot"/><div><b>کترینگ نمونه</b><small>پلن حرفه‌ای</small></div><span className="chevron">⌄</span></div>
      <div className="nav-caption">منوی اصلی</div>
      <nav>{nav.map(({label, icon: Icon}) => <button key={label} className={`nav-link ${active === label ? 'active' : ''}`} onClick={() => setActive(label)}><Icon size={19}/><span>{label}</span>{label === 'سفارش‌ها' && <em>۸</em>}</button>)}</nav>
      <div className="sidebar-bottom"><div className="help-card"><span>به کمک نیاز دارید؟</span><small>راهنمای امپراتور را ببینید.</small><button onClick={() => setActive('راهنما')}>مشاهده راهنما <ArrowUpLeft size={14}/></button></div><div className="profile"><div className="avatar">م</div><div><b>مدیر مجموعه</b><small>مدیر کل</small></div><Settings size={17}/></div></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><div className="breadcrumb">امپراتور <span>/</span> <b>{active}</b></div><div className="top-actions"><div className="search"><Search size={17}/><input placeholder="جستجو در امپراتور..." aria-label="جستجو"/></div><button className="icon-button" aria-label="اعلان‌ها"><Bell size={19}/><i/></button><div className="date-chip">شنبه، ۲۸ شهریور ۱۴۰۵</div></div></header>
      <section className="content"><div className="page-heading"><div><div className="eyebrow">نمای کلی کسب‌وکار</div><h1>سلام، مدیر عزیز 👋</h1><p>وضعیت امروز مجموعه‌ات را در یک نگاه بررسی کن.</p></div><button className="primary-button" onClick={() => setActive('سفارش جدید')}><Plus size={18}/> ثبت سفارش جدید</button></div>
      <div className="stats-grid">{stats.map((s,i)=><article className="stat-card" key={s.label}><div className="stat-top"><span>{s.label}</span><span className={`stat-icon tone-${i}`}><ChartNoAxesCombined size={18}/></span></div><div className="stat-value">{s.value}<small>{s.unit}</small></div><div className="stat-foot"><span className={i===3?'muted':'positive'}>{s.change}</span><span>نسبت به روز قبل</span></div></article>)}</div>
      <div className="section-grid"><section className="panel sales-panel"><div className="panel-heading"><div><h2>روند فروش</h2><p>مقایسه عملکرد فروش در هفته جاری</p></div><select aria-label="بازه زمانی" defaultValue="week"><option value="week">۷ روز گذشته</option><option value="month">۳۰ روز گذشته</option></select></div><div className="chart-summary"><strong>۱۶۸,۴۰۰,۰۰۰ <small>تومان</small></strong><span className="positive">↑ ۱۲.۸٪</span></div><div className="chart" role="img" aria-label="نمودار نمونه فروش هفتگی"><div className="y-labels"><span>۵۰م</span><span>۳۵م</span><span>۲۰م</span><span>۵م</span></div><div className="chart-body"><div className="grid-lines"><i/><i/><i/><i/></div><svg viewBox="0 0 700 210" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7c6cf2" stopOpacity=".25"/><stop offset="100%" stopColor="#7c6cf2" stopOpacity="0"/></linearGradient></defs><path d="M0 160 C45 145 60 165 100 130 S170 100 200 125 S270 80 300 100 S370 130 400 75 S470 95 500 55 S570 85 600 35 S665 65 700 18 L700 210 L0 210Z" fill="url(#area)"/><path d="M0 160 C45 145 60 165 100 130 S170 100 200 125 S270 80 300 100 S370 130 400 75 S470 95 500 55 S570 85 600 35 S665 65 700 18" fill="none" stroke="#8172f3" strokeWidth="3" vectorEffect="non-scaling-stroke"/></svg><div className="x-labels"><span>یکشنبه</span><span>دوشنبه</span><span>سه‌شنبه</span><span>چهارشنبه</span><span>پنجشنبه</span><span>جمعه</span><span>شنبه</span></div></div></div></section>
      <section className="panel quick-panel"><div className="panel-heading"><div><h2>دسترسی سریع</h2><p>کارهای پرتکرار مجموعه</p></div></div><div className="quick-grid">{[{label:'ثبت سفارش',icon:ShoppingCart,tone:'purple'},{label:'مدیریت انبار',icon:Package,tone:'orange'},{label:'مشاهده آشپزخانه',icon:ChefHat,tone:'green'},{label:'افزودن مشتری',icon:Users,tone:'blue'}].map(({label,icon:Icon,tone})=><button key={label} onClick={()=>setActive(label)} className="quick-item"><span className={`quick-icon ${tone}`}><Icon size={21}/></span><b>{label}</b><ArrowUpLeft size={15}/></button>)}</div><div className="tip"><span>✦</span><div><b>نکته امپراتور</b><p>با بررسی گزارش فروش، می‌توانید تصمیم‌های دقیق‌تری برای خرید مواد اولیه بگیرید.</p></div></div></section></div>
      <section className="panel orders-panel"><div className="panel-heading"><div><h2>آخرین سفارش‌ها</h2><p>نمایش آخرین سفارش‌های ثبت‌شده</p></div><button className="text-button" onClick={()=>setActive('سفارش‌ها')}>مشاهده همه <ArrowUpLeft size={15}/></button></div><div className="table-wrap"><table><thead><tr><th>شماره سفارش</th><th>مشتری</th><th>نوع تحویل</th><th>مبلغ کل</th><th>وضعیت</th><th></th></tr></thead><tbody>{orders.map(o=><tr key={o.id}><td className="order-id">{o.id}</td><td>{o.customer}</td><td>{o.type}</td><td>{o.total} <small>تومان</small></td><td><span className={`status ${o.status==='تکمیل‌شده'?'done':o.status==='آماده تحویل'?'ready':o.status==='ثبت‌شده'?'new':''}`}><i/>{o.status}</span></td><td><button className="more-button" aria-label={`جزئیات ${o.id}`}>•••</button></td></tr>)}</tbody></table></div></section>
      <footer>© ۱۴۰۵ امپراتور <span>نسخه آزمایشی رابط کاربری · داده‌ها نمایشی هستند</span></footer>
      </section>
    </main>
  </div>;
}
