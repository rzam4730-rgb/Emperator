import React,{useState} from 'react';
import {AuthProvider,useAuth} from './auth/AuthProvider.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import MainLayout from './components/layout/MainLayout.jsx';

function Dashboard(){
 const {user}=useAuth();
 return <MainLayout active="داشبورد">
   <div className="page-head">
    <div>
     <span className="eyebrow">نمای کلی کسب‌وکار</span>
     <h1>سلام، {user?.first_name||'مدیر'} 👋</h1>
     <p>وضعیت امروز مجموعه‌تان را در یک نگاه بررسی کنید.</p>
    </div>
    <button className="primary">＋ ثبت سفارش جدید</button>
   </div>
   <div className="stats">
    <div className="stat-card"><b>فروش امروز</b><strong>—</strong></div>
    <div className="stat-card"><b>سفارش‌ها</b><strong>—</strong></div>
    <div className="stat-card"><b>مشتریان</b><strong>—</strong></div>
    <div className="stat-card"><b>موجودی</b><strong>—</strong></div>
   </div>
 </MainLayout>
}

function Root(){
 const [registerMode,setRegisterMode]=useState(false);
 const {isAuthenticated}=useAuth();
 if(isAuthenticated) return <Dashboard/>;
 return registerMode ? <><Register/><button className="auth-switch" onClick={()=>setRegisterMode(false)}>ورود</button></> : <><Login/><button className="auth-switch" onClick={()=>setRegisterMode(true)}>ثبت‌نام</button></>;
}

export default function App(){return <AuthProvider><Root/></AuthProvider>}
