# استقرار نسخه وب امپراتور

این پوشه نسخه Web/Cloud امپراتور را آماده می‌کند.

## معماری

- `web`: Nginx برای سرو فایل‌های Frontend و Reverse Proxy مسیر `/api/*`
- `api`: FastAPI
- SQLite فعلاً روی volume پایدار Docker نگهداری می‌شود.
- همان Frontend فعلی هم در Windows Desktop و هم در Web قابل استفاده است؛ bridge موجود در `subscription.js` درخواست‌های قدیمی `127.0.0.1:8000` را در حالت Web به مسیر same-origin `/api` تبدیل می‌کند.

## اجرا روی VPS

1. Docker و Docker Compose نصب باشد.
2. از ریشه پروژه:

```bash
cd deploy/web
cp .env.example .env
# مقدار EMPERATOR_JWT_SECRET را با یک رشته تصادفی طولانی جایگزین کنید.
docker compose up -d --build
```

3. در مرورگر دامنه VPS را باز کنید.
4. سلامت API:

```text
/api/health
```

## HTTPS

برای Production، جلوی Nginx داخلی یک Reverse Proxy با TLS (مثلاً Nginx/Caddy روی Host) قرار دهید یا TLS را مستقیماً به لایه وب اضافه کنید.

## مرحله Production بعدی

قبل از مقیاس تجاری، دیتابیس باید از SQLite به PostgreSQL مهاجرت کند و Secretها فقط از Environment/Secret Manager تأمین شوند. همچنین ZarinPal، Kavenegar و Provider واقعی AI باید در محیط Production فعال و تست شوند.
