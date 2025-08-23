
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

# ---------- Vehicles ----------

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
        rec_date_str = request.form.get("recorded_date","").strip()
        rec_date = None
        if rec_date_str:
            try:
                rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
            except:
                rec_date = None
        v = Vehicle(
            license_plate=request.form.get("license_plate","").strip(),
            brand=request.form.get("brand","").strip(),
            model=request.form.get("model","").strip(),
            owner_name=request.form.get("owner_name","").strip(),
            contact_info=request.form.get("contact_info","").strip(),
            color=request.form.get("color","").strip(),
            vin=request.form.get("vin","").strip(),
            recorded_date=rec_date or date.today(),
        )
        db.session.add(v); db.session.commit()
        flash("เพิ่มข้อมูลสำเร็จ", "success")
        return redirect(url_for("dashboard.vehicles_list"))
    return render_template("vehicle_form.html", v=None)

@dashboard_bp.route("/vehicles/<int:vid>/edit", methods=["GET", "POST"])
@login_required
def vehicles_edit(vid):
    v = Vehicle.query.get_or_404(vid)
    if request.method == "POST":
        rec_date_str = request.form.get("recorded_date","").strip()
        rec_date = None
        if rec_date_str:
            try:
                rec_date = datetime.strptime(rec_date_str, "%Y-%m-%d").date()
            except:
                rec_date = None
        v.license_plate = request.form.get("license_plate","").strip()
        v.brand = request.form.get("brand","").strip()
        v.model = request.form.get("model","").strip()
        v.owner_name = request.form.get("owner_name","").strip()
        v.contact_info = request.form.get("contact_info","").strip()
        v.color = request.form.get("color","").strip()
        v.vin = request.form.get("vin","").strip()
        v.recorded_date = rec_date or v.recorded_date
        db.session.commit()
        flash("บันทึกข้อมูลสำเร็จ", "success")
        return redirect(url_for("dashboard.vehicles_list"))
    return render_template("vehicle_form.html", v=v)

@dashboard_bp.route("/vehicles/<int:vid>/delete", methods=["POST"])
@login_required
def vehicles_delete(vid):
    v = Vehicle.query.get_or_404(vid)
    db.session.delete(v); db.session.commit()
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
        optional = {"color","vin","recorded_date"}
        cols = set([c.strip() for c in (reader.fieldnames or [])])
        if cols >= required:
            count = 0
            from datetime import datetime, date
            for row in reader:
                rec_date = None
                rd = (row.get("recorded_date") or "").strip()
                if rd:
                    try:
                        rec_date = datetime.strptime(rd, "%Y-%m-%d").date()
                    except:
                        rec_date = None
                v = Vehicle(
                    license_plate=row.get("license_plate","").strip(),
                    brand=row.get("brand","").strip(),
                    model=row.get("model","").strip(),
                    owner_name=row.get("owner_name","").strip(),
                    contact_info=row.get("contact_info","").strip(),
                    color=row.get("color","").strip() if "color" in cols else None,
                    vin=row.get("vin","").strip() if "vin" in cols else None,
                    recorded_date=rec_date,
                )
                db.session.add(v); count += 1
            db.session.commit()
            flash(f"อัปโหลดสำเร็จ {count} รายการ", "success")
            return redirect(url_for("dashboard.vehicles_list"))
        else:
            flash("หัวคอลัมน์ไม่ถูกต้อง ต้องมีอย่างน้อย license_plate,brand,model,owner_name,contact_info", "danger")
    return render_template("upload_form.html")

@dashboard_bp.route("/line/users/<int:uid>/update", methods=["POST"])
@login_required
def line_users_update(uid):
    u = LineUser.query.get_or_404(uid)
    u.display_name = (request.form.get("display_name","") or "").strip()
    db.session.commit()
    flash("บันทึกชื่อผู้ใช้แล้ว", "success")
    return redirect(url_for("dashboard.line_users_list"))

@dashboard_bp.route("/line/groups/<int:gid>/update", methods=["POST"])
@login_required
def line_groups_update(gid):
    g = LineGroup.query.get_or_404(gid)
    g.display_name = (request.form.get("display_name","") or "").strip()
    db.session.commit()
    flash("บันทึกชื่อกลุ่มแล้ว", "success")
    return redirect(url_for("dashboard.line_groups_list"))
