const API='http://127.0.0.1:8000/api';let products=[],cart=[];
const fa=n=>Number(n||0).toLocaleString('fa-IR');

async function api(p,o={},retry=true){
  const headers={'Content-Type':'application/json',...(o.headers||{})};
  if(typeof accessToken!=='undefined'&&accessToken) headers.Authorization=`Bearer ${accessToken}`;
  const r=await fetch(API+p,{...o,headers});
  if(r.status===401&&retry&&typeof refreshAccessToken==='function'&&await refreshAccessToken()) return api(p,o,false);
  if(!r.ok){let detail='خطا در درخواست';try{const x=await r.json();detail=x.detail||detail}catch(_){}throw Error(detail)}
  return r.json()
}

async function refresh(){
  products=await api('/products');
  ['products','productManager'].forEach(id=>{let e=document.getElementById(id);if(e){e.innerHTML=products.map(p=>`<button class="product" data-product="${p.id}"><span class="food">${p.icon||'🍽️'}</span><b>${p.name}</b><p>${p.category}</p><span class="price">${fa(p.price)} تومان</span></button>`).join('');e.querySelectorAll('[data-product]').forEach(b=>b.onclick=()=>add(+b.dataset.product))}});
  let d=await api('/dashboard'),b=document.querySelectorAll('#dashboard .stat-card b');
  if(b.length>2){b[0].innerHTML=fa(d.sales)+' <em>تومان</em>';b[1].textContent=fa(d.orders);b[2].textContent=fa(d.customers)}
}
function add(id){let p=products.find(x=>x.id===id),x=cart.find(x=>x.id===id);x?x.qty++:cart.push({...p,qty:1});renderCart()}
function renderCart(){let e=document.getElementById('cart'),t=document.getElementById('total'),s=0;if(!e||!t)return;e.innerHTML=cart.length?cart.map(x=>{s+=x.price*x.qty;return `<div class="rank"><span>${x.name} × ${x.qty}</span><strong>${fa(x.price*x.qty)}</strong><button data-remove="${x.id}">×</button></div>`}).join(''):'سبد سفارش خالی است';t.textContent=fa(s)+' تومان';e.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{cart=cart.filter(x=>x.id!==+b.dataset.remove);renderCart()})}
async function checkout(){if(!cart.length)return alert('ابتدا محصولی اضافه کنید');try{let o=await api('/orders',{method:'POST',body:JSON.stringify({items:cart.map(x=>({product_id:x.id,quantity:x.qty})),payment_method:'نقدی'})});cart=[];renderCart();await refresh();alert('سفارش #'+o.id+' با موفقیت ذخیره شد')}catch(e){alert(e.message||'خطا در ثبت سفارش')}}
function showPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));document.getElementById(id)?.classList.add('active');document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.page===id));window.scrollTo(0,0);document.getElementById('moreMenu')?.classList.remove('show')}
document.addEventListener('DOMContentLoaded',()=>{document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>showPage(b.dataset.page));document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>showPage(b.dataset.go));document.getElementById('moreBtn')?.addEventListener('click',()=>document.getElementById('moreMenu').classList.toggle('show'));document.getElementById('checkoutBtn')?.addEventListener('click',checkout);renderCart()});
