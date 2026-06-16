#!/usr/bin/env python3
"""
arXiv에서 AI 분야 최신 논문 자동 수집 → 한국어 1줄 요약 → 블로그 포스트 자동 생성
매일 GitHub Actions cron으로 실행
"""

import os, json, re, time
from datetime import datetime, timezone, timedelta

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog", "_posts")

# 환경변수 (GitHub Actions secrets)
GK = os.environ.get("GROQ_API_KEY", "gsk_***PLACEHOLDER***")

ARXIV_QUERIES = [
    "cat:cs.AI",  # Artificial Intelligence
    "cat:cs.LG",  # Machine Learning
    "cat:cs.CV",  # Computer Vision
    "cat:cs.CL",  # NLP
]

def fetch_arxiv_papers(query="cat:cs.AI", max_results=8):
    """arXiv API에서 최신 논문 가져오기"""
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET

    base = "http://export.arxiv.org/api/query?"
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = base + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"arxiv err: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    root = ET.fromstring(data)
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        title = re.sub(r"\s+", " ", title)
        url_p = entry.find("atom:id", ns).text.strip()
        summary = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        summary = re.sub(r"\s+", " ", summary)[:1500]
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)]
        published = entry.find("atom:published", ns).text.strip()

        # arXiv ID 추출 (예: 2506.12345)
        arxiv_id = url_p.split("/")[-1]

        papers.append({
            "id": arxiv_id,
            "title": title,
            "summary": summary,
            "authors": authors[:5],
            "url": url_p,
            "published": published,
        })
    return papers


def translate_to_korean(title, abstract):
    """Groq API로 한국어 1줄 요약"""
    import requests
    prompt = f"""You are translating an AI paper title and abstract into Korean. Respond ONLY in the exact format below, no extra text.

[FIRST LINE FORMAT — start with "한국어 제목:"]
한국어 제목: <Korean translated title>

한국어 한 줄 요약: <30자 이내 핵심 idea 요약>

주요 기여:
- <contribution 1>
- <contribution 2>
- <contribution 3>

적용 분야: <field name>

English title: {title}

English abstract: {abstract[:1500]}"""

    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GK}", "Content-Type": "application/json"},
            json={
                "model": "qwen/qwen3-32b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=60)
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  translate err: {e}")
    # 실패시 영문 fallback
    return f"영문 제목: {title}\n\n영문 초록: {abstract[:500]}"


def parse_translation(text, fallback_title=""):
    """모델 출력 파싱 — 한국어 섹션 키워드가 없으면 fallback"""
    out = {"ko_title": "", "summary": "", "contributions": [], "field": ""}
    cur_section = None
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("한국어 제목:"):
            cur_section = "ko_title"
            out["ko_title"] = line.replace("한국어 제목:", "").strip()
        elif line.startswith("한국어 한 줄 요약") or "한 줄 요약" in line:
            cur_section = "summary"
            out["summary"] = line.split(":", 1)[-1].strip()
        elif line.startswith("주요 기여"):
            cur_section = "contributions"
        elif line.startswith("적용 분야"):
            cur_section = "field"
            out["field"] = line.replace("적용 분야:", "").strip()
        elif line.startswith(("•", "-", "*", "1.", "2.", "3.")):
            if cur_section == "contributions":
                out["contributions"].append(line.lstrip("•-*0123456789. ").strip())
    if not out["ko_title"] or len(out["ko_title"]) < 5:
        out["ko_title"] = fallback_title[:200] if fallback_title else "AI 논문"
    return out


def make_post(paper, translation):
    """마크다운 블로그 포스트 생성"""
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    parsed = parse_translation(translation, fallback_title=paper["title"])

    front_matter = f"""---
layout: post
title: "{parsed['ko_title'][:200]}"
date: {today} 09:00:00 +0900
categories: [ai, paper]
tags: [arxiv, {paper['id']}]
arxiv_id: {paper['id']}
description: "{parsed['summary'][:200]}"
---

# {parsed['ko_title']}

> **한 줄 요약:** {parsed['summary']}

**분야:** {parsed['field'] or 'AI/머신러닝'}

## 📝 영문 원제

**{paper['title']}**

## 🎯 주요 기여

{chr(10).join(f'- {c}' for c in parsed['contributions'][:5]) if parsed['contributions'] else '- (자동 추출 실패 — 영문 초록 참고)'}

## 📚 원문 초록

> {paper['summary']}

## ✍️ 저자

{', '.join(paper['authors'])}{' 외' if len(paper['authors']) == 5 else ''}

## 🔗 원문 보기

- [arXiv: {paper['id']}]({paper['url']})
- [PDF 다운로드](https://arxiv.org/pdf/{paper['id']})

---

*본 글은 AI 모델(Qwen3-32B)이 arXiv에서 매일 자동으로 수집·요약한 것입니다.*
*원문 정확성이 중요한 경우 항상 PDF 원문을 직접 확인하세요.*
"""
    return front_matter


def make_index_update(posts):
    """blog/index.html 인덱스 페이지 (기존 Jekyll이 자동 생성하지만 fallback)"""
    pass


def main():
    print(f"실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"출력 디렉토리: {OUT_DIR}")

    os.makedirs(OUT_DIR, exist_ok=True)

    all_papers = []
    for q in ARXIV_QUERIES:
        papers = fetch_arxiv_papers(q, max_results=3)
        all_papers.extend(papers)
        time.sleep(3)  # arXiv API 매너

    # 중복 제거 (논문 ID 기준)
    seen = set()
    unique = []
    for p in all_papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    print(f"\n수집된 논문: {len(unique)}건")

    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    success = 0

    for paper in unique[:8]:
        # 같은 날 같은 arxiv_id 이미 있는지 확인
        filename = f"{today}-{paper['id'].replace('.', '-')}.md"
        out_path = os.path.join(OUT_DIR, filename)
        if os.path.exists(out_path):
            print(f"  [skip] {paper['id']} (이미 있음)")
            continue

        print(f"\n--- {paper['id']}: {paper['title'][:80]} ---")

        translation = translate_to_korean(paper["title"], paper["summary"])
        post = make_post(paper, translation)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(post)
        print(f"  ✅ 저장: {filename}")
        success += 1

        time.sleep(15)  # Groq rate limit 방지

    print(f"\n완료: {success}건 새 포스팅")


if __name__ == "__main__":
    main()