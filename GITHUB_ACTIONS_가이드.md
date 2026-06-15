# GitHub Actions 설정 가이드

## 1. GitHub Secrets 등록 (2개)

https://github.com/flffkaos-pixel/ai-lab-free-services/settings/secrets/actions

### Secret 1: GOOGLE_CREDENTIALS
```
이름: GOOGLE_CREDENTIALS
값: (credentials.json 파일 내용 전체를 복사해서 붙여넣기)
```

### Secret 2: HERMES_WEBHOOK_URL
```
이름: HERMES_WEBHOOK_URL
값: (Hermes가 받을 웹훅 URL — 아래 "웹훅 URL 만들기" 참고)
```

---

## 2. 웹훅 URL 만들기

### 방법 A: Telegram 봇 연동 (무료)
```
1. @BotFather로 봇 생성
2. 봇과 대화 시작 → 채팅 ID 확인
3. 웹훅 URL = "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text="
```

### 방법 B: Discord 웹훅 (무료)
```
1. Discord 채널 설정 → 연동 → 웹후크
2. URL 복사
3. 웹훅 URL = 복사한 Discord 웹훅 URL
```

### 방법 C: email로 보내기 (간단)
```
1. Hermes CronJob이 주기적으로 GitHub Actions 로그를 확인
2. 또는 지금처럼 Hermes 내부 CronJob이 직접 폴링
```

---

## 3. GitHub에 푸시

```bash
cd ~/free-services
git add -A
git commit -m "GitHub Actions 자동화 추가"
git push
```

---

## 4. 확인

https://github.com/flffkaos-pixel/ai-lab-free-services/actions

"check-applications" 워크플로우가 녹색이면 성공!

---

## 전체 흐름

```
GitHub Actions (30분 간격, 무료)
    ↓
check-applications.py 실행
    ↓
새 신청 발견 → Hermes에 웹훅 전송
    ↓
Hermes CronJob이 auto-review-pipeline 실행
    ↓
논문 분석 or 영업 시뮬 → 이메일 발송
```

PC 꺼져도 GitHub에서 계속 돌아갑니다.