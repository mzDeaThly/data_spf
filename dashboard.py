from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from models import Vehicle, LineUser, LineGroup, Admin, db
from utils import login_required, hash_password

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/admin")


@dashboard_bp.route("/")
@login_required
def index():
    counts = {
        "vehicles": Vehicle.query.count(),
        "line_users": LineUser.query.count(),
        "line_groups": LineGroup.query.count(),
        "admins": Admin.query.count(),
    }
    return render_template("dashboard.html", counts=counts)


# -----------------------------
# Vehicles
# -----------------------------
@dashboard_bp.route("/vehicles")
@login_required
def vehicles_list():
    q = request.args.get("q", "").strip()
    query = Vehicle.query
    if q:
        like = f"%{q}%"
        query = query.filter(Vehicle.license_plate.ilike(like))
    vehicles = query.order_by(Vehicle.id.desc()).limit(500).all()
    return render_template("vehicles_list.html", vehicles=vehicles, q=q)


@dashboard_bp.route("/vehicles/add", methods=["GET", "POST"])
@login_required
def vehicles_add():
    if request.method == "POST":
        rec_date_str = (request.form.get("recorded_date") or "").strip()
        rec_date = None
        if rec_date_str:
            try:
                rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
            except Exception:
                rec_date = None

        v = Vehicle(
            license_plate=(request.form.get("license_plate") or "").strip(),
            brand=(request.form.get("brand") or "").strip(),
            model=(request.form.get("model") or "").strip(),
            owner_name=(request.form.get("owner_name") or "").strip(),
            contact_info=(request.form.get("contact_info") or "").strip(),
            color=(request.form.get("color") or "").strip(),
            vin=(request.form.get("vin") or "").strip(),
            recorded_date=rec_date or date.today(),
        )
        db.session.add(v)
        db.session.commit()
        flash("เพิ่มข้อมูลสำเร็จ", "success")
        return redirect(url_for("dashboard.vehicles_list"))
    return render_template("vehicle_form.html", v=None)


@dashboard_bp.route("/vehicles/<int:vid>/edit", methods=["GET", "POST"])
@login_required
def vehicles_edit(vid):
    v = Vehicle.query.get_or_404(vid)
    if request.method == "POST":
        rec_date_str = (request.form.get("recorded_date") or "").strip()
        rec_date = None
        if rec_date_str:
            try:
                rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
            except Exception:
                rec_date = None

        v.license_plate = (request.form.get("license_plate") or "").strip()
        v.brand = (request.form.get("brand") or "").strip()
        v.model = (request.form.get("model") or "").strip()
        v.owner_name = (request.form.get("owner_name") or "").strip()
        v.contact_info = (request.form.get("contact_info") or "").strip()
        v.color = (request.form.get("color") or "").strip()
        v.vin = (request.form.get("vin") or "").strip()
        v.recorded_date = rec_date or v.recorded_date

        db.session.commit()
        flash("บันทึกข้อมูลสำเร็จ", "success")
        return redirect(url_for("dashboard.vehicles_list"))
    return render_template("vehicle_form.html", v=v)


@dashboard_bp.route("/vehicles/<int:vid>/delete", methods=["POST"])
@login_required
def vehicles_delete(vid):
    v = Vehicle.query.get_or_404(vid)
    db.session.delete(v)
    db.session.commit()
    flash("ลบข้อมูลแล้ว", "info")
    return redirect(url_for("dashboard.vehicles_list"))


@dashboard_bp.route("/vehicles/upload", methods=["GET", "POST"])
@login_required
def vehicles_upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            flash("กรุณาเลือกไฟล์ CSV", "warning")
            return redirect(url_for("dashboard.vehicles_upload"))

        import csv, io
        stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
        reader = csv.DictReader(stream)

        required = {"license_plate", "brand", "model", "owner_name", "contact_info"}
        cols = set([c.strip() for c in (reader.fieldnames or [])])

        if not (cols >= required):
            flash(
                "หัวคอลัมน์ไม่ถูกต้อง ต้องมีอย่างน้อย license_plate,brand,model,owner_name,contact_info",
                "danger",
            )
            return redirect(url_for("dashboard.vehicles_upload"))

        count = 0
        for row in reader:
            rd_text = (row.get("recorded_date") or "").strip()
            rec_date = None
            if rd_text:
                try:
                    rec_date = datetime.strptime(rd_text, "%Y-%m-%d").date()
                except Exception:
                    rec_date = None

            v = Vehicle(
                license_plate=(row.get("license_plate") or "").strip(),
                brand=(row.get("brand") or "").strip(),
                model=(row.get("model") or "").strip(),
                owner_name=(row.get("owner_name") or "").strip(),
                contact_info=(row.get("contact_info") or "").strip(),
                color=(row.get("color") or "").strip() if "color" in cols else None,
                vin=(row.get("vin") or "").strip() if "vin" in cols else None,
                recorded_date=rec_date,
            )
            db.session.add(v)
            count += 1

        db.session.commit()
        flash(f"อัปโหลดสำเร็จ {count} รายการ", "success")
        return redirect(url_for("dashboard.vehicles_list"))

    return render_template("upload_form.html")


# -----------------------------
# LINE Users
# -----------------------------
@dashboard_bp.route("/line/users")
@login_required
def line_users_list():
    users = LineUser.query.order_by(LineUser.id.desc()).all()
    return render_template("line_users_list.html", users=users)


@dashboard_bp.route("/line/users/add", methods=["POST"])
@login_required
def line_users_add():
    uid = (request.form.get("line_user_id") or "").strip()
    active = request.form.get("is_active") == "on"
    dname = (request.form.get("display_name") or "").strip()
    if uid:
        u = LineUser(line_user_id=uid, is_active=active, display_name=dname)
        db.session.add(u)
        db.session.commit()
        flash("เพิ่ม User สำเร็จ", "success")
    else:
        flash("กรุณากรอก LINE UserID", "warning")
    return redirect(url_for("dashboard.line_users_list"))


@dashboard_bp.route("/line/users/<int:uid>/toggle", methods=["POST"])
@login_required
def line_users_toggle(uid):
    u = LineUser.query.get_or_404(uid)
    u.is_active = not u.is_active
    db.session.commit()
    flash("อัปเดตสถานะแล้ว", "info")
    return redirect(url_for("dashboard.line_users_list"))


@dashboard_bp.route("/line/users/<int:uid>/delete", methods=["POST"])
@login_required
def line_users_delete(uid):
    u = LineUser.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    flash("ลบ User แล้ว", "info")
    return redirect(url_for("dashboard.line_users_list"))


@dashboard_bp.route("/line/users/<int:uid>/update", methods=["POST"])
@login_required
def line_users_update(uid):
    u = LineUser.query.get_or_404(uid)
    u.display_name = (request.form.get("display_name") or "").strip()
    db.session.commit()
    flash("บันทึกชื่อผู้ใช้แล้ว", "success")
    return redirect(url_for("dashboard.line_users_list"))


# -----------------------------
# LINE Groups
# -----------------------------
@dashboard_bp.route("/line/groups")
@login_required
def line_groups_list():
    groups = LineGroup.query.order_by(LineGroup.id.desc()).all()
    return render_template("line_groups_list.html", groups=groups)


@dashboard_bp.route("/line/groups/add", methods=["POST"])
@login_required
def line_groups_add():
    gid = (request.form.get("line_group_id") or "").strip()
    active = request.form.get("is_active") == "on"
    dname = (request.form.get("display_name") or "").strip()
    if gid:
        g = LineGroup(line_group_id=gid, is_active=active, display_name=dname)
        db.session.add(g)
        db.session.commit()
        flash("เพิ่ม Group สำเร็จ", "success")
    else:
        flash("กรุณากรอก LINE GroupID", "warning")
    return redirect(url_for("dashboard.line_groups_list"))


@dashboard_bp.route("/line/groups/<int:gid>/toggle", methods=["POST"])
@login_required
def line_groups_toggle(gid):
    g = LineGroup.query.get_or_404(gid)
    g.is_active = not g.is_active
    db.session.commit()
    flash("อัปเดตสถานะแล้ว", "info")
    return redirect(url_for("dashboard.line_groups_list"))


@dashboard_bp.route("/line/groups/<int:gid>/delete", methods=["POST"])
@login_required
def line_groups_delete(gid):
    g = LineGroup.query.get_or_404(gid)
    db.session.delete(g)
    db.session.commit()
    flash("ลบ Group แล้ว", "info")
    return redirect(url_for("dashboard.line_groups_list"))


@dashboard_bp.route("/line/groups/<int:gid>/update", methods=["POST"])
@login_required
def line_groups_update(gid):
    g = LineGroup.query.get_or_404(gid)
    g.display_name = (request.form.get("display_name") or "").strip()
    db.session.commit()
    flash("บันทึกชื่อกลุ่มแล้ว", "success")
    return redirect(url_for("dashboard.line_groups_list"))


# -----------------------------
# Admins
# -----------------------------
@dashboard_bp.route("/admins")
@login_required
def admins_list():
    admins = Admin.query.order_by(Admin.id.desc()).all()
    return render_template("admins_list.html", admins=admins)


@dashboard_bp.route("/admins/add", methods=["GET", "POST"])
@login_required
def admins_add():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if not username or not password:
            flash("กรุณากรอกข้อมูลให้ครบ", "warning")
            return redirect(url_for("dashboard.admins_add"))
        a = Admin(username=username, password=hash_password(password))
        db.session.add(a)
        db.session.commit()
        flash("เพิ่มผู้ดูแลระบบสำเร็จ", "success")
        return redirect(url_for("dashboard.admins_list"))
    return render_template("admin_form.html", admin=None)


@dashboard_bp.route("/admins/<int:aid>/edit", methods=["GET", "POST"])
@login_required
def admins_edit(aid):
    admin = Admin.query.get_or_404(aid)
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()
        if username:
            admin.username = username
        if password:
            admin.password = hash_password(password)
        db.session.commit()
        flash("บันทึกข้อมูลสำเร็จ", "success")
        return redirect(url_for("dashboard.admins_list"))
    return render_template("admin_form.html", admin=admin)


@dashboard_bp.route("/admins/<int:aid>/delete", methods=["POST"])
@login_required
def admins_delete(aid):
    admin = Admin.query.get_or_404(aid)
    if Admin.query.count() <= 1:
        flash("ไม่สามารถลบผู้ดูแลระบบคนสุดท้ายได้", "danger")
        return redirect(url_for("dashboard.admins_list"))
    db.session.delete(admin)
    db.session.commit()
    flash("ลบผู้ดูแลระบบแล้ว", "info")
    return redirect(url_for("dashboard.admins_list"))
