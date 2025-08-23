import base64, hmac, hashlib, json, requests
from datetime import date
from flask import Blueprint, request, current_app
from models import Vehicle, LineUser, LineGroup
from utils import has_line_permission
from flex_templates import to_flex_message

line_bp = Blueprint("line", __name__, url_prefix="/line")

MAX_AGE_DAYS = 35  # แสดงเฉพาะข้อมูลที่บันทึกมาแล้วไม่เกิน N วัน


def verify_line_signature(body: bytes, signature_header: str, channel_secret: str) -> bool:
    mac = hmac.new(channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature_header)


@line_bp.route("/webhook", methods=["POST"])
def webhook():
    channel_secret = current_app.config.get("LINE_CHANNEL_SECRET", "")
    access_token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not channel_secret or not access_token:
        return "LINE config missing", 500

    body = request.get_data()
    signature = request.headers.get("X-Line-Signature", "")
    if not verify_line_signature(body, signature, channel_secret):
        return "Bad signature", 400

    payload = request.get_json(silent=True) or {}
    events = payload.get("events", [])

    for ev in events:
        if ev.get("type") != "message":
            continue
        if ev["message"].get("type") != "text":
            continue

        source = ev.get("source", {})
        source_type = source.get("type")  # 'user' | 'group' | 'room'
        user_id = source.get("userId")
        group_id = source.get("groupId") if source_type in ("group", "room") else None

        text = (ev["message"].get("text") or "").strip()
        lower = text.lower()

        # ---------- คำสั่งสาธารณะ (ข้ามการตรวจสิทธิ์) ----------
        if lower == "/userid":
            if user_id:
                rec = LineUser.query.filter_by(line_user_id=user_id).first()
                dname = rec.display_name if rec and rec.display_name else None
                msg = f"UserID ของคุณ: {user_id}\n" + (f"ชื่อที่ตั้งค่า: {dname}" if dname else "(ยังไม่ได้ตั้งชื่อ)")
            else:
                msg = "ไม่พบ UserID"
            reply(access_token, ev["replyToken"], [{"type": "text", "text": msg}])
            continue

        if lower == "/groupid":
            if group_id:
                rec = LineGroup.query.filter_by(line_group_id=group_id).first()
                dname = rec.display_name if rec and rec.display_name else None
                msg = f"GroupID ของห้องนี้: {group_id}\n" + (f"ชื่อที่ตั้งค่า: {dname}" if dname else "(ยังไม่ได้ตั้งชื่อ)")
            else:
                msg = "คำสั่งนี้ใช้ได้ในกลุ่ม/ห้องเท่านั้น — เชิญบอทเข้ากลุ่มแล้วพิมพ์ /groupid อีกครั้ง"
            reply(access_token, ev["replyToken"], [{"type": "text", "text": msg}])
            continue
        # -------------------------------------------------------

        # ตรวจสิทธิ์หลังจากเช็คคำสั่งสาธารณะแล้วเท่านั้น
        if not has_line_permission(user_id, group_id):
            reply(access_token, ev["replyToken"], [{"type": "text", "text": "คุณไม่มีสิทธิ์ใช้งานระบบนี้ กรุณาติดต่อผู้ดูแล"}])
            continue

        # ค้นหาทะเบียน (และกรองอายุข้อมูล ≤ MAX_AGE_DAYS)
        like = f"%{text}%"
        candidates = (
            Vehicle.query.filter(Vehicle.license_plate.ilike(like))
            .order_by(Vehicle.id.desc())
            .limit(20)
            .all()
        )

        # กรองเฉพาะคันที่มี recorded_date และไม่เกิน MAX_AGE_DAYS
        today = date.today()
        fresh = []
        for v in candidates:
            rd = getattr(v, "recorded_date", None)
            if rd is None:
                continue
            if (today - rd).days <= MAX_AGE_DAYS:
                fresh.append(v)

        if not fresh:
            reply(access_token, ev["replyToken"], [{"type": "text", "text": "ไม่พบข้อมูลทะเบียนที่ค้นหา"}])
            continue

        # >>> เปลี่ยนตรงนี้: ส่งเฉพาะ Flex Message ไม่มีข้อความสรุปนำหน้า <<<
        flex = to_flex_message(fresh[:10])
        reply(access_token, ev["replyToken"], [{
            "type": "flex",
            "altText": f"ผลการค้นหา {len(fresh[:10])} รายการ",
            "contents": flex
        }])

    return "ok"


def reply(access_token: str, reply_token: str, messages: list):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    data = {"replyToken": reply_token, "messages": messages}
    try:
        r = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        r.raise_for_status()
    except Exception as e:
        current_app.logger.exception("LINE reply error: %s", e)
