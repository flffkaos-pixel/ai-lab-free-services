import os, json, requests, smtplib
from email.mime.text import MIMEText
from datetime import datetime

S = "1q-3_iJEWNfQr8a2N45aEH0hqCXUpOp2m59gNpM38K4w"
C = "last_check.json"
E = "flffkaos@gmail.com"
P = "tvck udjx egic ukdg"
G = "ghp_UP...T4vG"

def mail(to, subj, body):
    try:
        m = MIMEText(body)
        m["Subject"] = subj
        m["From"] = E
        m["To"] = to
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.login(E, P)
        s.send_message(m)
        s.quit()
        return True
    except:
        return False

def rows():
    u = f"https://docs.google.com/spreadsheets/d/{S}/export?format=csv"
    r = requests.get(u)
    r.raise_for_status()
    text = r.text.replace('\r', '')
    lines = text.strip().split("\n")
    h = lines[0].split(",")
    out = []
    for line in lines[1:]:
        if not line.strip():
            continue
        v, cur, q = [], "", False
        for ch in line:
            if ch == '"':
                q = not q
            elif ch == ',' and not q:
                v.append(cur.strip().strip('"'))
                cur = ""
            else:
                cur += ch
        v.append(cur.strip().strip('"'))
        out.append(dict(zip(h, v)))
    return out

def main():
    data = rows()
    lp = 0
    if os.path.exists(C):
        lp = json.load(open(C)).get("last_row", 0)
    new = data[lp:]
    if not new:
        return
    for i, row in enumerate(new):
        name = row.get("이름", "익명")
        email = row.get("이메일", "")
        title = row.get("논문 제목", "")
        content = row.get("논문파일 업로드", "")
        rn = lp + i + 2
        print(f"[{rn}행] {name} - {title}")
        # GitHub Issue
        try:
            resp = requests.post(
                "https://api.github.com/repos/flffkaos-pixel/ai-lab-free-services/issues",
                headers={"Authorization": f"token {G}"},
                json={"title": f"[논문] {name} - {title}", "body": f"{name}\n{email}\n{content}", "labels": ["paper-review"]}
            )
            if resp.status_code == 201:
                print(f"  OK")
        except:
            pass
        # 너에게
        mail(E, f"[신청] {name} - {title}", f"{name}\n{email}\n{title}")
    json.dump({"last_row": len(data)}, open(C, "w"))

if __name__ == "__main__":
    main()