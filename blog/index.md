---
layout: default
permalink: /
---
# AI 논문 한 줄

매일 새로운 AI/머신러닝 논문을 한국어로 한 줄씩 요약해 드립니다.

## 📚 최신 논문

{% for post in site.posts limit:20 %}
- [{{ post.title }}]({{ post.url | relative_url }}) — _{{ post.date | date: "%Y-%m-%d" }}_
{% endfor %}

## 🤖 작동 방식

1. 매일 0시 (UTC, 한국 시간 오전 9시)에 자동 실행됩니다
2. arXiv에서 `cs.AI`, `cs.LG`, `cs.CV`, `cs.CL` 분야 최신 논문을 수집합니다
3. Groq AI의 Qwen3-32B 모델이 한국어 한 줄 요약을 만듭니다
4. Jekyll로 즉시 정적 사이트에 포스팅합니다

## 💡 왜 만들었나요?

해외 AI 논문을 빠르게 파악하고 싶은 한국 학생·연구자·개발자를 위해 만들었습니다.
매일 8건씩 받아 1년이면 3,000건 가까운 논문을 한국어로 살펴보실 수 있어요.

## 🔗 소스

- GitHub: [flffkaos-pixel/ai-lab-free-services](https://github.com/flffkaos-pixel/ai-lab-free-services)
- 자동화: [.github/workflows/blog.yml](https://github.com/flffkaos-pixel/ai-lab-free-services/blob/master/.github/workflows/blog.yml)