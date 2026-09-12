const products=[
{id:1,name:'چلوکباب مخصوص',category:'غذا',price:285000,icon:'🥩'},
{id:2,name:'زرشک‌پلو با مرغ',category:'غذا',price:190000,icon:'🍗'},
{id:3,name:'قورمه‌سبزی',category:'غذا',price:175000,icon:'🍲'},
{id:4,name:'جوجه کباب',category:'غذا',price:210000,icon:'🍢'},
{id:5,name:'نوشابه',category:'نوشیدنی',price:25000,icon:'🥤'},
{id:6,name:'دوغ محلی',category:'نوشیدنی',price:35000,icon:'🥛'},
{id:7,name:'کیک شکلاتی',category:'دسر',price:65000,icon:'🍰'},
{id:8,name:'سالاد فصل',category:'پیش‌غذا',price:55000,icon:'🥗'}];
let cart=[];const fa=n=>Number(n).toLocaleString('fa-IR');
function renderProducts(target='products'){const el=document.getElementById(target);if(!el)return;el.innerHTML=products.map(p=>`<button class="product" data-product="${p.id}"><span class="food">${p.icon}</span><b>${p.name}</b><p>${p.category}</p><span class="price">${fa(p.price)} تومان</span></button>`).join('');el.querySelectorAll('[data-product]').forEach(b=>b.onclick=()=>add(+b.dataset.product))}
function add(id){const p=products.find(x=>x.id===id);const x=cart.find(x=>x.id===id);x?x.qty++:cart.push({...p,qty:1});renderCart()}
function renderCart(){const el=document.getElementById('cart'),total=document.getElementById('total');if(!el)return;let sum=0;el.innerHTML=cart.length?cart.map(x=>{sum+=x.price*x.qty;return `<div class="rank"><span>${x.name} × ${x.qty}</span><strong>${fa(x.price*x.qty)}</strong><button class="remove" data-remove="${x.id}">×</button></div>`}).join(''):'سبد سفارش خالی است';if(total)total.textContent=fa(sum)+' تومان';el.querySelectorAll('[data-remove]').forEach(b=>b.onclick=()=>{cart=cart.filter(x=>x.id!==+b.dataset.remove);renderCart()})}
function showPage(id){document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));const p=document.getElementById(id);if(p)p.classList.add('active');document.querySelectorAll('.nav').forEach(n=>n.classList.toggle('active',n.dataset.page===id));window.scrollTo(0,0);document.getElementById('moreMenu').classList.remove('show')}
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>showPage(b.dataset.page));document.querySelectorAll('[data-go]').forEach(b=>b.onclick=()=>showPage(b.dataset.go));document.getElementById('moreBtn').onclick=()=>document.getElementById('moreMenu').classList.toggle('show');document.getElementById('checkoutBtn').onclick=()=>{if(!cart.length)return alert('ابتدا محصولی به سفارش اضافه کنید');cart=[];renderCart();alert('سفارش با موفقیت ثبت شد')};renderProducts();renderProducts('productManager');renderCart();