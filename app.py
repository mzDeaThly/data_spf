
from flask import Flask
from config import Config
from models import db, Admin
from auth import auth_bp
from dashboard import dashboard_bp
from linebot_app import line_bp
from utils import hash_password
import os

def auto_migrate(app):
    from sqlalchemy import inspect
    with app.app_context():
        engine = db.engine
        insp = inspect(engine)
        if "vehicles" in insp.get_table_names():
            cols = {c['name'] for c in insp.get_columns("vehicles")}
            to_add = []
            if "color" not in cols:
                to_add.append(("color", "VARCHAR(64)"))
            if "vin" not in cols:
                to_add.append(("vin", "VARCHAR(64)"))
            if "recorded_date" not in cols:
                to_add.append(("recorded_date", "DATE"))
            if to_add:
                dialect = engine.dialect.name  # 'sqlite', 'mysql', 'postgresql'
                for name, dtype in to_add:
                    if dialect == "sqlite":
                        ddl = f"ALTER TABLE vehicles ADD COLUMN {name} {dtype};"
                    else:
                        ddl = f"ALTER TABLE vehicles ADD COLUMN {name} {dtype}"
                        if dialect == "mysql":
                            ddl += " NULL"
                        ddl += ";"
                    try:
                        with engine.connect() as conn:
                            conn.exec_driver_sql(ddl)
                    except Exception:
                        # คอลัมน์อาจถูกเพิ่มไว้แล้ว หรือสิทธิ์ไม่พอ — ข้ามไป
                        pass

        if "line_users" in insp.get_table_names():
            cols_u = {c['name'] for c in insp.get_columns("line_users")}
            if "display_name" not in cols_u:
                try:
                    with engine.connect() as conn:
                        conn.exec_driver_sql("ALTER TABLE line_users ADD COLUMN display_name VARCHAR(128);")
                except Exception:
                    pass

        if "line_groups" in insp.get_table_names():
            cols_g = {c['name'] for c in insp.get_columns("line_groups")}
            if "display_name" not in cols_g:
                try:
                    with engine.connect() as conn:
                        conn.exec_driver_sql("ALTER TABLE line_groups ADD COLUMN display_name VARCHAR(128);")
                except Exception:
                    pass

def ensure_initial_admin():
    # สร้างแอดมินอัตโนมัติรอบแรก ถ้ายังไม่มีผู้ดูแลระบบเลย
    username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password = os.getenv("ADMIN_PASSWORD", "admin123").strip()
    if not username or not password:
        return
    if Admin.query.count() == 0:
        a = Admin(username=username, password=hash_password(password))
        db.session.add(a); db.session.commit()

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        ensure_initial_admin()
    auto_migrate(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(line_bp)

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
