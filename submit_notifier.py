#!/usr/bin/env python3
"""
구글 시트를 신청서로 사용 — Google Forms 없이 작동.
누구나 구글 시트에 신청 정보를 입력하면 → GitHub Issue 생성 → Hermes가 처리.

사용법:
1. 구글 시트 만들기 (sheets.google.com)
2. 시트를 "링크가 있는 모든 사용자에게 편집 권한"으로 공유
3. 시트 ID를 SPREADSHEET_ID에 입력
4. GitHub Token을 GH_TOKEN에 입력
5. python submit_notifier.py

또는 이 스크립트를 CronJob에 연결하면 30분마다 자동 체크.
"""

import os
import json
import re
import requests
from datetime import datetime

# ============================================================
# 설정 — 여기만 수정하면 됨
# ============================================================
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"  # 구글 시트 URL에서 /d/.../edit 부분
GH_TOKEN = "YOUR_GITHUB_TOKEN"          # GitHub Settings → Developer settings → Tokens
GH_REPO = "flffkaos-pixel/ai-lab-free-services"
LAST_CHECK = os.path.expanduser("~/.hermes/last_sheet_check.json")
# ============================================================

def get_sheet_data():
    """구글 시트를 공개 CSV로 읽기"""
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"
    resp = requests.get(url)
    resp.raise_for_status()
    lines = resp.text.strip().split("\n")
    header = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        values = []
        current = ""
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
            elif ch == ',' and not in_quotes:
                values.append(current.strip().strip('"'))
                current = ""
            else:
                current += ch
        values.append(current.strip().strip('"'))
        row = dict(zip(header, values))
        rows.append(row)
    return rows

def main():
    try:
        rows = get_sheet_data()
    except Exception as e:
        print(f"ERROR: 시트 읽기 실패: {e}")
        return

    if not rows:
        return

    # 마지막 체크 위치
    last_processed = 0
    if os.path.exists(LAST_CHECK):
        with open(LAST_CHECK) as f:
            last_processed = json.load(f).get("last_row", 0)

    new_rows = rows[last_processed:]

    if not new_rows:
        return

    # 새 신청 → GitHub Issues 생성
    for i, row in enumerate(new_rows):
        row_num = last_processed + i + 2  # 1부터 시작 + 헤더

        name = row.get("이름", row.get("name", "익명"))
        email = row.get("이메일", row.get("email", ""))
        service = row.get("서비스", row.get("service", "기타"))
        content = row.get("내용", row.get("content", row.get("message", "")))

        # 제목: [서비스] 이름
        if "논문" in service or "review" in service.lower():
            label = "paper-review"
        elif "영업" in service or "sales" in service.lower():
            label = "sales-sim"
        else:
            label = "general"

        title = f"[{service}] {name}님 신청"
        body = f"""## 새 신청 접수

- **이름:** {name}
- **이메일:** {email}
- **서비스:** {service}
- **접수일:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

### 내용
{content}
"""
        # GitHub Issue 생성
        url = f"https://api.github.com/repos/{GH_REPO}/issues"
        headers = {
            "Authorization": f"token {GH_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": title,
            "body": body,
            "labels": ["new-application", label]
        }

        try:
            resp = requests.post(url, headers=headers, json=data)
            if resp.status_code == 201:
                issue_url = resp.json()["html_url"]
                print(f"✅ [{row_num}행] {title} → {issue_url}")
            else:
                print(f"❌ [{row_num}행] 실패: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"❌ [{row_num}행] 오류: {e}")

    # 체크포인트 저장
    with open(LAST_CHECK, "w") as f:
        json.dump({"last_row": len(rows), "updated": datetime.now().isoformat()}, f)

    print(f"처리 완료: {len(new_rows)}건 신규")

if __name__ == "__main__":
    main()