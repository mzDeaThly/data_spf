
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
