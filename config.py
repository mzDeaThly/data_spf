
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
