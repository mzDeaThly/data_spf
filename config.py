import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LINE creds
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")

    # ปรับจำนวนวันหมดอายุผลค้นหาได้ผ่าน ENV (ค่าเริ่มต้น 35)
    LINE_MAX_AGE_DAYS = int(os.getenv("LINE_MAX_AGE_DAYS", "35"))
