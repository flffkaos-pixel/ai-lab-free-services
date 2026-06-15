#!/usr/bin/env python3
"""results.json 읽어서 신청자에게 이메일 발송"""
import json, os, smtplib
from email.mime.text import MIMEText

RDIR = os.path.dirname(os.path.abspath(__file__))
E = "flffkaos@gmail.com"
P = "tvck udjx egic ukdg"

def send(to, subj, body):
    try:
        m = MIMEText(body, "plain", "utf-8")
        m["Subject"] = subj
        m["From"] = E
        m["To"] = to
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.login(E, P)
        s.send_message(m)
        s.quit()
        print(f"  ✅ 발송: {to}")
        return True
    except Exception as e:
        print(f"  ❌ 실패: {e}")
        return False

def main():
    path = os.path.join(RDIR, "results.json")
    if not os.path.exists(path):
        print("results.json 없음")
        return
    data = json.load(open(path, encoding="utf-8"))
    for item in data:
        name = item.get("name", "익명")
        email = item.get("email", "")
        title = item.get("title", "")
        review = item.get("review", "")
        if not email or not review:
            continue
        body = f"""{name}님, 신청하신 논문 리뷰 결과입니다.

━━━━━━━━━━━━━━━━━━━━━━━
📜 {title}
📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}
━━━━━━━━━━━━━━━━━━━━━━━

{review}

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 본 리뷰는 AI의 1차 분석입니다. 투고 전 반드시 지도교수님 확인을 받으세요.
AI 연구소 드림
"""
        send(email, f"[논문 리뷰] {title}", body)
    os.remove(path)
    print("완료")

if __name__ == "__main__":
    main()