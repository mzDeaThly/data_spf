from datetime import date

def format_thai_be(d: date | None) -> str:
    if not d:
        return "-"
    return f"{d.day:02d}/{d.month:02d}/{d.year + 543}"

def days_since(d: date | None) -> str:
    if not d:
        return "-"
    delta = (date.today() - d).days
    return f"{delta} วัน"

def vehicle_bubble(v):
    return {
      "type": "bubble",
      "body": {
        "type": "box",
        "layout": "vertical",
        "spacing": "sm",
        "contents": [
          {"type":"text","text":"ทะเบียน: " + (v.license_plate or "-"),"weight":"bold","size":"lg"},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"ยี่ห้อ","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.brand or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"รุ่น","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.model or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"ผู้ใช้งาน","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.owner_name or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"ติดต่อ","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.contact_info or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"สีรถ","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.color or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"เลขตัวถัง","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": (v.vin or "-"),"size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"บันทึกเมื่อ","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": format_thai_be(getattr(v, "recorded_date", None)), "size":"sm","wrap":True,"flex":5}
          ]},
          {"type":"box","layout":"baseline","contents":[
            {"type":"text","text":"ผ่านมา","size":"sm","color":"#aaaaaa","flex":2},
            {"type":"text","text": days_since(getattr(v, "recorded_date", None)), "size":"sm","wrap":True,"flex":5}
          ]}
        ]
      }
    }

def to_flex_message(vehicles):
    bubbles = [vehicle_bubble(v) for v in vehicles]
    if len(bubbles) == 1:
        return bubbles[0]
    return {"type":"carousel","contents": bubbles}
