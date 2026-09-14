"""ZarinPal gateway adapter for Emperator.

Configuration is environment-based: ZARINPAL_MERCHANT_ID and optionally
ZARINPAL_SANDBOX=1. The adapter uses the v4 request/verify endpoints.
"""
import os
import urllib.request
import json
from .payment import PaymentGateway, PaymentStart, PaymentVerify

class ZarinPalGateway(PaymentGateway):
    def __init__(self):
        self.merchant=os.getenv('ZARINPAL_MERCHANT_ID','').strip()
        self.sandbox=os.getenv('ZARINPAL_SANDBOX','0')=='1'
    def _base(self):
        return 'https://sandbox.zarinpal.com/pg/rest/WebGate' if self.sandbox else 'https://api.zarinpal.com/pg/v4/payment'
    def _post(self,path,payload):
        req=urllib.request.Request(self._base()+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=20) as r: return json.loads(r.read().decode())
    def create(self, amount, description, callback_url, metadata=None):
        if not self.merchant: raise RuntimeError('ZARINPAL_MERCHANT_ID تنظیم نشده است')
        data={'merchant_id':self.merchant,'amount':int(amount),'description':description,'callback_url':callback_url}
        if metadata: data['metadata']=metadata
        body=self._post('/request.json',data)
        code=((body.get('data') or {}).get('code'))
        authority=((body.get('data') or {}).get('authority'))
        if code not in (100,101) or not authority: raise RuntimeError('خطا در ایجاد پرداخت زرین‌پال')
        host='https://sandbox.zarinpal.com/pg/StartPay/' if self.sandbox else 'https://www.zarinpal.com/pg/StartPay/'
        return PaymentStart(authority=authority,payment_url=host+authority)
    def verify(self, amount, authority):
        if not self.merchant: return PaymentVerify(False,None,'ZARINPAL_MERCHANT_ID تنظیم نشده است')
        body=self._post('/verify.json',{'merchant_id':self.merchant,'amount':int(amount),'authority':authority})
        data=body.get('data') or {}; code=data.get('code'); ref=data.get('ref_id')
        return PaymentVerify(code in (100,101),str(ref) if ref else None,str(data.get('message','')))
