
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Admin
from utils import hash_password, verify_password

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        admin = Admin.query.filter_by(username=username).first()
        if admin and verify_password(admin.password, password):
            session["admin_id"] = admin.id
            session.permanent = True
            flash("เข้าสู่ระบบสำเร็จ", "success")
            return redirect(url_for("dashboard.index"))
        flash("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบแล้ว", "info")
    return redirect(url_for("auth.login"))
