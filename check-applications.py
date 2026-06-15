#!/usr/bin/env python3
"""
구글폼 응답 시트를 30분마다 확인하고, 새로운 신청이 있으면 Hermes에 전달합니다.

설정:
1. 구글 클라우드 콘솔에서 서비스 계정 생성 → credentials.json 다운로드
2. 구글폼 응답 시트를 해당 서비스 계정과 공유
3. credentials.json을 ~/.hermes/credentials.json에 저장
4. SPREADSHEET_NAME을 실제 시트 이름으로 변경

사용법:
    python check-applications.py
    # 신규 신청 있으면 → stdout에 JSON 출력 → Hermes CronJob이 읽음
    # 신규 신청 없으면 → stdout에 아무것도 출력 안 함 → CronJob 조용히 넘어감
"""

import os
import json
import sys
from datetime import datetime

LAST_CHECK = os.path.expanduser("~/.hermes/last_check.json")
SPREADSHEET_NAME = "AI연구소-신청서"  # ← 실제 구글 시트 이름으로 변경
CREDENTIALS = os.path.expanduser("~/.hermes/credentials.json")

# 구글 시트 접근 (gspread 라이브러리 필요)
# pip install gspread oauth2client
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    records = sheet.get_all_records()
except Exception as e:
    print(json.dumps({"error": str(e)}, ensure_ascii=False))
    sys.exit(0)

# 마지막 체크 위치 확인
last_row = 0
if os.path.exists(LAST_CHECK):
    with open(LAST_CHECK, "r") as f:
        last_check = json.load(f)
    last_row = last_check.get("last_row", 0)

# 새로 추가된 행만 추출
new_entries = records[last_row:]

if not new_entries:
    # 새 신청 없음 → stdout에 아무것도 출력하지 않음
    # → Hermes CronJob이 조용히 넘어감
    sys.exit(0)

# 새 신청 있음 → row 번호 추가해서 JSON 출력
for i, entry in enumerate(new_entries):
    entry["_row"] = last_row + i + 2  # 1부터 시작 + 헤더행 보정

# 마지막 체크 위치 업데이트
with open(LAST_CHECK, "w") as f:
    json.dump(
        {"last_row": len(records), "updated": datetime.now().isoformat()}, f
    )

# Hermes가 읽을 JSON 출력
# CronJob이 이 출력을 context로 받아서 처리
print(json.dumps(new_entries, ensure_ascii=False, indent=2))