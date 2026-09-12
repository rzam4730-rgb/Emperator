from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Emperator API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

products=[{"id":1,"name":"چلوکباب کوبیده","category":"غذای ایرانی","price":220000},{"id":2,"name":"زرشک پلو با مرغ","category":"غذای ایرانی","price":210000},{"id":3,"name":"پیتزا مخصوص","category":"فست فود","price":250000},{"id":4,"name":"برگر امپراتور","category":"فست فود","price":230000},{"id":5,"name":"قهوه اسپرسو","category":"کافه","price":90000},{"id":6,"name":"آبمیوه طبیعی","category":"نوشیدنی","price":80000}]
orders=[]
@app.get("/api/health")
def health(): return {"status":"ok","app":"Emperator"}
@app.get("/api/products")
def get_products(): return products
@app.get("/api/orders")
def get_orders(): return list(reversed(orders))
@app.post("/api/orders")
def create_order(payload:dict):
    total=0; lines=[]
    for item in payload.get("items",[]):
        p=next((x for x in products if x["id"]==item.get("product_id")),None)
        if p:
            q=max(1,int(item.get("quantity",1))); total+=p["price"]*q; lines.append({"product_id":p["id"],"name":p["name"],"quantity":q,"price":p["price"]})
    order={"id":len(orders)+1,"status":"جدید","items":lines,"total":total}; orders.append(order); return order
@app.get("/api/dashboard")
def dashboard():
    return {"orders":len(orders),"sales":sum(x["total"] for x in orders),"customers":0,"busy_tables":0}
