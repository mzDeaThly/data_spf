import base64, hmac, hashlib, json, requests, os
from datetime import date
from flask import Blueprint, request, current_app
from models import Vehicle, LineUser, LineGroup, AuditLog, db, ensure_auditlog_columns
from utils import has_line_permission
from flex_templates import to_flex_message

line_bp = Blueprint("line", __name__, url_prefix="/line")

def _verify_signature(body: bytes, signature_header: str, channel_secret: str) -> bool:
    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature_header)

def _get_max_age_days() -> int:
    try:
        return int(current_app.config.get("LINE_MAX_AGE_DAYS", os.getenv("LINE_MAX_AGE_DAYS", "35")))
    except Exception:
        return 35

def _fetch_line_display_name(access_token: str, source_type: str, user_id: str | None, group_id: str | None) -> str | None:
    """
    ดึงชื่อสมาชิกผู้พิมพ์จาก LINE
    - 1:1   -> GET /v2/bot/profile/{userId}
    - group -> GET /v2/bot/group/{groupId}/member/{userId}
    - room  -> GET /v2/bot/room/{roomId}/member/{userId}
    """
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        if source_type == "user" and user_id:
            url = f"https://api.line.me/v2/bot/profile/{user_id}"
        elif source_type == "group" and user_id and group_id:
            url = f"https://api.line.me/v2/bot/group/{group_id}/member/{user_id}"
        elif source_type == "room" and user_id and group_id:
            url = f"https://api.line.me/v2/bot/room/{group_id}/member/{user_id}"
        else:
            return None
        r = requests.get(url, headers=headers, timeout=6)
        if r.ok:
            data = r.json()
            return data.get("displayName")
    except Exception:
        current_app.logger.exception("fetch display name error")
    return None

def _write_log(source_type, user_id, group_id, text, matched=None, allowed=True,
               actor_display_name=None, context_display_name=None):
    try:
        log = AuditLog(
            source_type=source_type,
            line_user_id=user_id,
            line_group_id=group_id,
            query_text=(text or "")[:255],
            matched=matched,
            allowed=allowed,
            actor_display_name=actor_display_name,
            context_display_name=context_display_name,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("audit log error")

@line_bp.route("/webhook", methods=["POST"])
def webhook():
    channel_secret = current_app.config.get("LINE_CHANNEL_SECRET", "")
    access_token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not channel_secret or not access_token:
        return "LINE config missing", 500

    # ตรวจและเพิ่มคอลัมน์ใหม่ของ audit_logs ถ้ายังไม่มี
    try:
        ensure_auditlog_columns()
    except Exception:
        current_app.logger.exception("ensure_auditlog_columns failed")

    body = request.get_data()
    signature = request.headers.get("X-Line-Signature", "")
    if not _verify_signature(body, signature, channel_secret):
        return "Bad signature", 400

    payload = request.get_json(silent=True) or {}
    events = payload.get("events", [])

    for ev in events:
        if ev.get("type") != "message": 
            continue
        if ev["message"].get("type") != "text":
            continue

        source = ev.get("source", {})
        stype = source.get("type")          # 'user' | 'group' | 'room'
        user_id = source.get("userId")
        group_id = source.get("groupId") if stype in ("group", "room") else None

        text = (ev["message"].get("text") or "").strip()
        lower = text.lower()

        # ---------- คำสั่งสาธารณะ (ไม่ลง log การค้นหา) ----------
        if lower == "/userid":
            if user_id:
                rec = LineUser.query.filter_by(line_user_id=user_id).first()
                dname = rec.display_name if rec and rec.display_name else None
                msg = f"UserID ของคุณ: {user_id}\n" + (f"ชื่อที่ตั้งค่า: {dname}" if dname else "(ยังไม่ได้ตั้งชื่อ)")
            else:
                msg = "ไม่พบ UserID"
            _reply(access_token, ev["replyToken"], [{"type": "text", "text": msg}])
            continue

        if lower == "/groupid":
            if group_id:
                rec = LineGroup.query.filter_by(line_group_id=group_id).first()
                dname = rec.display_name if rec and rec.display_name else None
                msg = f"GroupID ของห้องนี้: {group_id}\n" + (f"ชื่อที่ตั้งค่า: {dname}" if dname else "(ยังไม่ได้ตั้งชื่อ)")
            else:
                msg = "คำสั่งนี้ใช้ได้ในกลุ่ม/ห้องเท่านั้น — เชิญบอทเข้ากลุ่มแล้วพิมพ์ /groupid อีกครั้ง"
            _reply(access_token, ev["replyToken"], [{"type": "text", "text": msg}])
            continue
        # ---------------------------------------------------------

        # ชื่อที่ตั้งค่าจากระบบ (context)
        user_rec = LineUser.query.filter_by(line_user_id=user_id).first() if user_id else None
        group_rec = LineGroup.query.filter_by(line_group_id=group_id).first() if group_id else None
        context_name = (user_rec.display_name if (stype == "user" and user_rec and user_rec.display_name) else
                        group_rec.display_name if (stype in ("group","room") and group_rec and group_rec.display_name) else
                        None)

        # ชื่อสมาชิกผู้พิมพ์จาก LINE
        actor_name = _fetch_line_display_name(access_token, stype, user_id, group_id)

        # ตรวจสิทธิ์
        if not has_line_permission(user_id, group_id):
            _write_log(stype, user_id, group_id, text, matched=None, allowed=False,
                       actor_display_name=actor_name, context_display_name=context_name)
            _reply(access_token, ev["replyToken"], [{"type": "text", "text": "คุณไม่มีสิทธิ์ใช้งานระบบนี้ กรุณาติดต่อผู้ดูแล"}])
            continue

        # ค้นหา
        like = f"%{text}%"
        candidates = (
            Vehicle.query.filter(Vehicle.license_plate.ilike(like))
            .order_by(Vehicle.id.desc())
            .limit(20)
            .all()
        )

        # กรองอายุ
        max_age = _get_max_age_days()
        today = date.today()
        fresh = []
        for v in candidates:
            rd = getattr(v, "recorded_date", None)
            if rd is None:
                continue
            if (today - rd).days <= max_age:
                fresh.append(v)

        # Log
        _write_log(stype, user_id, group_id, text, matched=len(fresh), allowed=True,
                   actor_display_name=actor_name, context_display_name=context_name)

        if not fresh:
            _reply(access_token, ev["replyToken"], [
                {"type": "text", "text": f"ไม่พบข้อมูลทะเบียนที่ค้นหา หรือข้อมูลเกิน {max_age} วันแล้ว"}
            ])
            continue

        # เฉพาะ Flex
        flex = to_flex_message(fresh[:10])
        _reply(access_token, ev["replyToken"], [{
            "type": "flex",
            "altText": f"ผลการค้นหา {len(fresh[:10])} รายการ",
            "contents": flex
        }])

    return "ok"

def _reply(access_token: str, reply_token: str, messages: list):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"replyToken": reply_token, "messages": messages}
    try:
        r = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        r.raise_for_status()
    except Exception as e:
        current_app.logger.exception("LINE reply error: %s", e)
