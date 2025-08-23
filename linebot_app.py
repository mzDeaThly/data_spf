
import base64, hmac, hashlib, json, requests
from flask import Blueprint, request, current_app
from models import Vehicle, LineUser, LineGroup
from utils import has_line_permission
from flex_templates import to_flex_message

line_bp = Blueprint("line", __name__, url_prefix="/line")

MAX_AGE_DAYS = 35

def verify_line_signature(body: bytes, signature_header: str, channel_secret: str) -> bool:
    mac = hmac.new(channel_secret.encode('utf-8'), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode('utf-8')
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
        user_id = source.get("userId")
        group_id = source.get("groupId") if source.get("type") in ("group","room") else None

        if not has_line_permission(user_id, group_id):
            reply_text = "คุณไม่มีสิทธิ์ใช้งานระบบนี้ กรุณาติดต่อผู้ดูแล"
            reply(access_token, ev["replyToken"], [{"type":"text","text":reply_text}])
            continue

        query_text = ev["message"].get("text","").strip()
        if not query_text:
            reply(access_token, ev["replyToken"], [{"type":"text","text":"กรุณาพิมพ์ทะเบียนรถที่ต้องการค้นหา"}])
            continue

        like = f"%{query_text}%"
        candidates = Vehicle.query.filter(Vehicle.license_plate.ilike(like)).order_by(Vehicle.id.desc()).limit(20).all()

        # Filter out entries with missing recorded_date or older than MAX_AGE_DAYS
        fresh = []
        today = __import__('datetime').date.today()
        for v in candidates:
            rd = getattr(v, "recorded_date", None)
            if rd is None:
                continue
            diff = (today - rd).days
            if diff <= MAX_AGE_DAYS:
                fresh.append(v)

        if not fresh:
            reply(access_token, ev["replyToken"], [{"type":"text","text":"ไม่พบข้อมูลทะเบียนที่ค้นหา หรือข้อมูลเกิน 35 วันแล้ว"}])
            continue

        # Compose a summary text (for the first item)
        first = fresh[0]
        rd = first.recorded_date
        be_year = rd.year + 543
        rd_text = f"{rd.day:02d}/{rd.month:02d}/{be_year}"
        diff_days = (today - rd).days
        summary = (
            f"บันทึกข้อมูลทะเบียนรถ {first.license_plate} วันที่ {rd_text}\n"
            f"ผู้ใช้ เรียกดูข้อมูลทะเบียนรถ {query_text}\n"
            f"(ผ่านการบันทึกข้อมูลมาแล้ว {diff_days} วัน)"
        )

        flex = to_flex_message(fresh[:10])
        reply(access_token, ev["replyToken"], [
            {"type":"text","text": summary},
            {
                "type": "flex",
                "altText": f"ผลการค้นหา {len(fresh[:10])} รายการ",
                "contents": flex
            }
        ])

    return "ok"

def reply(access_token: str, reply_token: str, messages: list):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {"replyToken": reply_token, "messages": messages}
    try:
        r = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        r.raise_for_status()
    except Exception as e:
        current_app.logger.exception("LINE reply error: %s", e)
