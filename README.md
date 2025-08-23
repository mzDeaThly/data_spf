
# ระบบทะเบียนรถภายในบริษัท (UI ภาษาไทยเต็มระบบ)

**อัปเดต**
- เพิ่มฟิลด์: สีรถ (color), เลขตัวถัง (vin), วันที่บันทึกข้อมูลในระบบ (recorded_date)
- รองรับ MySQL (ใช้ `mysql+pymysql://`)
- Bulk Upload รองรับคอลัมน์ใหม่

## การติดตั้งแบบย่อ
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# ตั้งค่า DATABASE_URL เป็น MySQL หรือปล่อยว่างเพื่อใช้ SQLite

python -c "from app import create_app; app=create_app(); ctx=app.app_context(); ctx.push(); from models import db; db.create_all(); print('DB created.')"
python seed_admin.py
flask --app app run --host 0.0.0.0 --port 8000
```

## ตัวอย่าง DATABASE_URL (MySQL)
```
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname?charset=utf8mb4
```

## รูปแบบ CSV
```
license_plate,brand,model,owner_name,contact_info,color,vin,recorded_date
```
> `recorded_date` ใช้รูปแบบ `YYYY-MM-DD`

## Auto-Seed แอดมิน (อัตโนมัติรอบแรก)
แอปจะตรวจสอบว่าในตาราง `admins` มีผู้ใช้หรือไม่ หากยังไม่มี จะสร้างผู้ใช้แรกโดยใช้ค่าใน ENV:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

> ทำงานอัตโนมัติเมื่อแอปบูทครั้งแรกของฐานข้อมูลลูกนั้น ๆ (idempotent — ถ้ามีแล้วจะไม่เพิ่มซ้ำ)

## ความถาวรของข้อมูล (ไม่หายเมื่อรีสตาร์ท/รีดีพลอย)
- **บน Render:** กรุณาใช้ฐานข้อมูลภายนอกที่คงทน (เช่น Managed MySQL) แล้วตั้ง `DATABASE_URL` ชี้ไปยังอินสแตนซ์ดังกล่าว ข้อมูลจะไม่ผูกกับไฟล์บนดิสก์ของแอปและไม่หายหลังรีดีพลอย
- **บนเครื่อง/เซิร์ฟเวอร์ของคุณ:** ใช้ `docker-compose.yml` ที่ให้มา (มีบริการ MySQL + named volume `fleet_mysql_data`) ข้อมูลจะเก็บในโวลุ่มถาวร ไม่หายเมื่อคอนเทนเนอร์รีสตาร์ทหรือรีบิลด์

## ใช้งาน docker-compose (ถาวร)
```bash
docker-compose up -d --build
# เปิดเว็บ: http://localhost:8000/admin
# MySQL จะรันบนพอร์ต 3306 และข้อมูลอยู่ในโวลุ่มชื่อ fleet_mysql_data
```

## ตั้งค่า Render (สรุป)
- Build: `pip install -r requirements.txt`
- Start: `gunicorn wsgi:app -b 0.0.0.0:8000 --workers 2 --threads 4`
- ENV ที่ต้องมี: `SECRET_KEY`, `DATABASE_URL`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`

## ใช้ Render Postgres (Managed)
- โปรเจกต์นี้เตรียม `render.yaml` ไว้ให้: เมื่อกด Deploy แบบ Blueprint จะสร้างฐานข้อมูล Postgres อัตโนมัติ
- ตัวแอปอ่านค่า `DATABASE_URL` จาก connectionString ของฐานข้อมูลนั้นโดยตรง
- ต้องเพิ่ม `SECRET_KEY`, `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN` ใน Environment ของ Service

### ไดรเวอร์ Postgres
- ติดตั้งแล้ว: `psycopg2-binary`
- รูปแบบ URL: `postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME`

### การย้ายจาก SQLite/MySQL เดิม
- แก้ `.env` ให้ชี้ `DATABASE_URL` เป็น Postgres
- รันแอปขึ้นมา ระบบจะ `db.create_all()` ให้ และมี `auto_migrate()` สำหรับคอลัมน์ใหม่ของตาราง `vehicles`
- ถ้ามีข้อมูลเดิม ให้ทำการ migrate/ETL แยก (เช่น dump จาก MySQL แล้ว import เข้า Postgres)
