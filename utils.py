from flask import session, redirect, url_for, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from models import LineUser, LineGroup

def hash_password(plain: str) -> str:
    return generate_password_hash(plain)

def verify_password(hashed: str, plain: str) -> bool:
    return check_password_hash(hashed, plain)

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("กรุณาเข้าสู่ระบบก่อน", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

def has_line_permission(user_id: str | None, group_id: str | None) -> bool:
    # อนุญาตหาก (user_id ถูกเปิดสิทธิ์) หรือ (group_id ถูกเปิดสิทธิ์)
    from models import LineUser, LineGroup
    allowed = False
    if user_id:
        u = LineUser.query.filter_by(line_user_id=user_id, is_active=True).first()
        if u:
            allowed = True
    if group_id:
        g = LineGroup.query.filter_by(line_group_id=group_id, is_active=True).first()
        if g:
            allowed = True
    return allowed
