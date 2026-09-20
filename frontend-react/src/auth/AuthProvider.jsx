import React,{createContext,useContext,useEffect,useMemo,useState} from 'react';
import {login as loginRequest} from '../services/api.js';
const AuthContext=createContext(null);
export function AuthProvider({children}){const[accessToken,setAccessToken]=useState(()=>localStorage.getItem('emperator_access_token'));const[user,setUser]=useState(()=>{try{return JSON.parse(localStorage.getItem('emperator_user')||'null')}catch{return null}});
useEffect(()=>{if(accessToken)localStorage.setItem('emperator_access_token',accessToken);else localStorage.removeItem('emperator_access_token')},[accessToken]);
const signIn=async(phone,password)=>{const data=await loginRequest(phone,password);const token=data.access_token||data.token;if(!token)throw new Error('توکن ورود از سرور دریافت نشد.');setAccessToken(token);const current=data.user||data.me||{phone};setUser(current);localStorage.setItem('emperator_user',JSON.stringify(current));if(data.refresh_token)localStorage.setItem('emperator_refresh_token',data.refresh_token);return data};
const signOut=()=>{setAccessToken(null);setUser(null);['emperator_user','emperator_refresh_token'].forEach(k=>localStorage.removeItem(k))};
const value=useMemo(()=>({accessToken,user,isAuthenticated:!!accessToken,signIn,signOut}),[accessToken,user]);return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>}
export function useAuth(){const value=useContext(AuthContext);if(!value)throw new Error('useAuth must be used inside AuthProvider');return value}
