
import os
from dotenv import load_dotenv
from app import create_app
from models import db, Admin
from utils import hash_password

if __name__ == "__main__":
    load_dotenv()
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    app = create_app()
    with app.app_context():
        if not Admin.query.filter_by(username=username).first():
            a = Admin(username=username, password=hash_password(password))
            db.session.add(a); db.session.commit()
            print(f"Created admin: {username}")
        else:
            print("Admin already exists.")
