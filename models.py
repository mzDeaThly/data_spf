
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Vehicle(db.Model):
    __tablename__ = "vehicles"
    id = db.Column(db.Integer, primary_key=True)
    license_plate = db.Column(db.String(64), nullable=False, index=True)
    brand = db.Column(db.String(64))
    model = db.Column(db.String(64))
    owner_name = db.Column(db.String(128))
    contact_info = db.Column(db.String(128))
    color = db.Column(db.String(64))            # สีรถ
    vin = db.Column(db.String(64))              # เลขตัวถัง
    recorded_date = db.Column(db.Date)          # วันที่บันทึกข้อมูลในระบบ (YYYY-MM-DD)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LineUser(db.Model):
    __tablename__ = "line_users"
    id = db.Column(db.Integer, primary_key=True)
    line_user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    display_name = db.Column(db.String(128))  # ชื่อที่ตั้งค่า (ออปชัน)
    display_name = db.Column(db.String(128))  # ชื่อที่ตั้งค่า (ออปชัน)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class LineGroup(db.Model):
    __tablename__ = "line_groups"
    id = db.Column(db.Integer, primary_key=True)
    line_group_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    display_name = db.Column(db.String(128))  # ชื่อที่ตั้งค่า (ออปชัน)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Admin(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # hashed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    when = db.Column(db.DateTime, default=datetime.utcnow, index=True)  # เวลา (UTC)

    source_type = db.Column(db.String(10))         # 'user' | 'group' | 'room'
    line_user_id = db.Column(db.String(64), index=True)
    line_group_id = db.Column(db.String(64), index=True)

    query_text = db.Column(db.String(255), index=True)
    matched = db.Column(db.Integer)                # จำนวนผลลัพธ์ที่แสดง
    allowed = db.Column(db.Boolean, default=True)  # ผ่านสิทธิ์หรือไม่

    # --- ฟิลด์ใหม่ ---
    actor_display_name = db.Column(db.String(120))    # ชื่อสมาชิกผู้พิมพ์ (จาก LINE)
    context_display_name = db.Column(db.String(120))  # ชื่อที่ตั้งค่า (จากตาราง line_users / line_groups)

def ensure_auditlog_columns():
    """
    เพิ่มคอลัมน์ใหม่ในตาราง audit_logs หากยังไม่มี (ไม่ต้องใช้ Alembic ก็ได้)
    เรียกใช้ตอนมี request ครั้งแรกๆ เพื่อความปลอดภัย
    """
    engine = db.engine
    insp = inspect(engine)
    if "audit_logs" not in insp.get_table_names():
        # ยังไม่เคยสร้างตาราง — ให้ db.create_all() สร้างตามโมเดลนี้
        return

    existing = {c["name"] for c in insp.get_columns("audit_logs")}
    to_add = []
    if "actor_display_name" not in existing:
        to_add.append(("actor_display_name", "VARCHAR(120)"))
    if "context_display_name" not in existing:
        to_add.append(("context_display_name", "VARCHAR(120)"))

    if not to_add:
        return

    ddl_tpl = "ALTER TABLE audit_logs ADD COLUMN {col} {typ};"
    with engine.begin() as conn:
        for col, typ in to_add:
            conn.exec_driver_sql(ddl_tpl.format(col=col, typ=typ))
