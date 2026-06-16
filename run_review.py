"""
AI 연구소 - 완전 자동 논문 리뷰 시스템
구글폼 응답 → 시트 → Google Drive PDF 다운로드 → qwen3 분석 → 이메일 발송
"""

import os, json, requests, smtplib, csv, io, subprocess, tempfile, re
from email.mime.text import MIMEText
from datetime import datetime
import time

# 자격 증명 (환경변수 → 기본값 순)
SID = "1q-3_iJEWNfQr8a2N45aEH0hqCXUpOp2m59gNpM38K4w"
EM = os.environ.get("GMAIL_USER", "flffkaos@gmail.com")
PW = os.environ.get("GMAIL_APP_PASSWORD", "tvck_PLACEHOLDER")
GK = os.environ.get("GROQ_API_KEY", "gsk_PLACEHOLDER")
CHK = "last_check.json"

# ============================================
def send_mail(to, subj, body):
    try:
        m = MIMEText(body, "plain", "utf-8")
        m["Subject"] = subj
        # 발신자 표시는 "AI 연구소 <이메일>" 형식 (답장 가능)
        m["From"] = f"AI 연구소 <{EM}>"
        m["To"] = to
        # Reply-To도 동일하게 (답장 시 AI 연구소로 오게)
        m["Reply-To"] = f"AI 연구소 <{EM}>"
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        s.login(EM, PW)
        s.send_message(m)
        s.quit()
        return True
    except Exception as e:
        print(f"  mail err: {e}")
        return False

# ============================================
def get_rows():
    r = requests.get(f"https://docs.google.com/spreadsheets/d/{SID}/export?format=csv")
    r.raise_for_status()
    r.encoding = 'utf-8'
    text = r.text.replace('\r', '').strip()
    reader = csv.reader(io.StringIO(text))
    all_rows = list(reader)
    if not all_rows:
        return []
    headers = [h.strip() for h in all_rows[0]]
    rows = []
    for vals in all_rows[1:]:
        if all(v.strip() == '' for v in vals):
            continue
        if len(vals) < len(headers):
            vals += [''] * (len(headers) - len(vals))
        rows.append(dict(zip(headers, vals)))
    return rows

# ============================================
def download_paper(url):
    try:
        m = re.search(r'/d/([a-zA-Z0-9_-]+)', url) or re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if not m:
            return None
        file_id = m.group(1)
        d_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        resp = requests.get(d_url, allow_redirects=True, timeout=45)
        ctype = resp.headers.get('Content-Type', '')
        if 'pdf' in ctype.lower() or resp.content[:4] == b'%PDF':
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(resp.content)
                tmp = f.name
            try:
                r = subprocess.run(['pdftotext', '-layout', tmp, '-'],
                                   capture_output=True, text=True, timeout=45)
                return r.stdout if r.stdout else None
            finally:
                os.unlink(tmp)
        elif 'text' in ctype or 'html' in ctype:
            return resp.text[:20000]
        return None
    except Exception as e:
        print(f"  download err: {e}")
        return None

# ============================================
def strip_think(text):
    """qwen3가 출력하는 <think>...</think> 블록 제거"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

# ============================================
def is_valid_email(email):
    if not email or '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2 or not parts[1] or '.' not in parts[1]:
        return False
    return True

# ============================================
def review_paper(title, content):
    content = (content or "").strip()
    downloaded = ""

    if "drive.google.com" in content:
        print(f"  📥 Google Drive 다운로드 시도...")
        downloaded = download_paper(content) or ""
        if len(downloaded) > 200:
            print(f"  ✅ {len(downloaded)}자 받음")
        else:
            print(f"  ⚠️ 다운로드 실패/부족")

    if len(downloaded) > 200:
        actual, label = downloaded[:1200], "[첨부된 논문 원문 발췌]"
    elif content and len(content) > 20:
        actual, label = content[:1200], "[신청자가 제출한 글]"
    else:
        actual, label = "", "[원문 미첨부 - 제목만 기반 일반 분석]"

    prompt = f"""당신은 20년 경력의 학술지 심사위원입니다.

━━━━━━━━━━━━━━━━━━━━━━━
📜 {title}
📄 {label}
{actual}
━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 지시: <think> 등 사고 과정 출력 금지. 심사 결과만 작성.

[1단계] 분야 자동 감지 후 분야별 가이드 적용:
자연과학/의학 / 공학·컴퓨터 / 인문사회 / 교육학 / 예술·디자인 중 하나.

[2단계] 6영역 평가 (각 영역 200자 이내, 구체적 개선안 포함)

**1. 논리 구조** - 연구질문 명확성, 가설 falsifiable, 방법론 정합성, 결론 데이터 충실성
**2. 가독성** - 초록의 목적·방법·결과 명시, 핵심 아이디어 1~2문장, IMRaD 흐름
**3. 편향** - 데이터 편중, selection bias, 자기 인용, 일반화 한계
**4. 방법론** - 통계 검정 적합성, 표본 크기, 다중비교 보정, p-hacking, 재현성
   * 통계 추천: 두 그룹 t-test/Mann-Whitney, 3그룹 ANOVA, 관계 Pearson/Spearman, 예측 Linear/Logistic
**5. 영문 초록** - 한글/영문 일치, IEEE/ACM/APA 기준, 영문 표기 일관성
**6. 종합 평가**
- 🔴 Critical / 🟡 Recommended / 🟢 Optional
- 📊 Accept / Minor / Major / Reject
- 🎯 Accept까지 예상 라운드 수

[3단계] 분야별 총평 + 추천 저널 (KCI/SCIE 등급별) 1~2문장.

토큰 절약 위해 전체 4000자 이내로 작성."""

    for attempt in range(2):  # 최대 2회 시도 (rate limit 대응)
        try:
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GK}", "Content-Type": "application/json"},
                json={
                    "model": "qwen/qwen3-32b",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "max_tokens": 3500
                    },
                timeout=180)
            data = resp.json()
            if "choices" in data:
                return strip_think(data["choices"][0]["message"]["content"])
            # Rate limit이면 대기 후 재시도
            if resp.status_code in (429, 503) and attempt == 0:
                wait = 150
                print(f"  ⏳ Rate limit, {wait}초 대기 후 재시도...")
                time.sleep(wait)
                continue
            print(f"  API err: {data}")
            return None
        except Exception as e:
            print(f"  API err: {e}")
            return None
    return None

# ============================================
def main():
    print("=" * 50)
    print("AI 연구소 - 자동 논문 리뷰")
    print(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    data = get_rows()
    print(f"시트에서 {len(data)}행 수신")

    lp = 0
    if os.path.exists(CHK):
        lp = json.load(open(CHK)).get("last_row", 0)
    new = data[lp:]
    print(f"신규 신청: {len(new)}건")

    if not new:
        print("처리할 신청 없음")
        return 0

    sent = 0
    failed = 0

    for i, row in enumerate(new):
        name = row.get("이름", "익명")
        email = row.get("이메일", "")
        title = row.get("논문 제목", "")
        content = row.get("논문파일 업로드", "")
        rn = lp + i + 2

        print(f"\n[{rn}행] {name} ({email}) - {title}")

        if not is_valid_email(email):
            print(f"  ⚠️ 이메일 형식 오류, 건너뜀")
            failed += 1
            continue

        result = review_paper(title, content)
        if not result:
            print(f"  ⚠️ 리뷰 생성 실패")
            failed += 1
            continue

        body = f"""{name}님, 안녕하세요.

신청하신 논문 리뷰 결과입니다.

📜 논문 제목: {title}
📅 심사 일자: {datetime.now().strftime('%Y-%m-%d')}
🤖 심사 모델: Qwen3-32B (via Groq)
━━━━━━━━━━━━━━━━━━━━━━━

{result}

━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 본 리뷰는 AI의 1차 분석입니다.
국제 저널 투고 전 반드시 지도교수님의 검토를 받으세요.

AI 연구소 드림
https://forms.gle/tRGWZd2xY6SCmtkw5"""

        if send_mail(email, f"[논문 리뷰] {title}", body):
            print(f"  ✅ 신청자 발송 완료: {email}")
            send_mail(EM, f"[완료] {name}", f"✅ {name}님 결과 발송\n논문: {title}")
            sent += 1
        else:
            print(f"  ❌ 발송 실패")
            failed += 1

        # 다음 요청 전 대기 (TPM rate limit 방지)
        if i < len(new) - 1:
            print(f"  ⏳ TPM 쿨다운 120초...")
            time.sleep(120)

    json.dump({"last_row": len(data), "updated": datetime.now().isoformat()},
              open(CHK, "w"), ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print(f"완료: 성공 {sent}건 / 실패 {failed}건")
    print("=" * 50)
    return sent

if __name__ == "__main__":
    main()