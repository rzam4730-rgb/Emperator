/* Emperator local ESC/POS printer integration. */
const EMPERATOR_PRINTER_URL='http://127.0.0.1:8765';

function escPosReceipt(order, items, paperMm=58){
  const width=paperMm===80?48:32;
  const enc=new TextEncoder();
  const out=[];
  const push=s=>out.push(...enc.encode(s));
  push('\x1b@');
  push('\x1b\x61\x01امپراتور\n\x1b\x61\x00');
  push('-'.repeat(width)+'\n');
  (items||[]).forEach(item=>{
    const qty=Math.max(1,Number(item.qty||item.quantity||1));
    const price=Number(item.price||0);
    const total=qty*price;
    const right=String(total.toLocaleString('fa-IR'));
    const left=`${qty}x ${item.name||''}`;
    push(left.slice(0,Math.max(1,width-right.length)).padEnd(Math.max(1,width-right.length),' ')+right+'\n');
  });
  push('-'.repeat(width)+'\n');
  const total=Number(order?.total||0).toLocaleString('fa-IR');
  push('جمع کل'.padEnd(Math.max(1,width-total.length),' ')+total+'\n\n\n');
  push('\x1d\x56\x00');
  return new Uint8Array(out);
}

async function printerHealth(){
  try{const r=await fetch(EMPERATOR_PRINTER_URL+'/health');return r.ok;}catch(_){return false;}
}

async function printReceipt(order, items, paperMm=58){
  const data=escPosReceipt(order,items,paperMm);
  const r=await fetch(EMPERATOR_PRINTER_URL+'/print',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:data});
  const result=await r.json().catch(()=>({ok:false,error:'پاسخ چاپگر نامعتبر است'}));
  if(!r.ok||!result.ok)throw Error(result.error||'چاپ رسید انجام نشد');
  return result;
}

(function wireReceiptPrinting(){
  if(typeof checkout!=='function')return;
  const originalCheckout=checkout;
  checkout=async function(){
    const receiptItems=(typeof cart!=='undefined'?cart:[]).map(x=>({name:x.name,price:x.price,quantity:x.qty}));
    try{
      const available=await printerHealth();
      await originalCheckout();
      if(available&&receiptItems.length){
        const total=receiptItems.reduce((s,x)=>s+Number(x.price||0)*Number(x.quantity||1),0);
        await printReceipt({total},receiptItems,58);
      }
    }catch(e){
      alert(e.message||'خطا در عملیات چاپ');
    }
  };
})();
