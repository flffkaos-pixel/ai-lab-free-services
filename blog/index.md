---
layout: default
permalink: /ai-lab-free-services/
---
# AI 논문 한 줄

매일 GitHub Actions가 자동으로 arXiv에서 AI 분야 최신 논문을 가져와서 한국어로 1줄 요약합니다.

## 📚 최신 논문

{% for post in site.posts limit:10 %}
- [{{ post.title }}]({{ post.url | relative_url }}) — _{{ post.date | date: "%Y-%m-%d" }}_
{% endfor %}

## 🤖 작동 방식

1. 매일 UTC 09:00 (한국 시간 18:00) 자동 실행
2. arXiv에서 cs.AI, cs.LG, cs.CV, cs.CL 분야 최신 논문 8건 수집
3. Groq AI (Qwen3-32B)로 한국어 1줄 요약
4. Jekyll 정적 사이트로 자동 포스팅

## 🔗 소스
- GitHub: https://github.com/flffkaos-pixel/ai-lab-free-services
- 자동화: `.github/workflows/blog.yml`