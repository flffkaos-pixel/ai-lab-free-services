#!/usr/bin/env python3
"""
arXiv → 한국어 요약 → Jekyll 블로그 + 분야별 페이지 자동 생성
"""

import os, json, re, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "blog", "_posts")
BLOG_DIR = os.path.join(ROOT, "blog")
GK = os.environ.get("GROQ_API_KEY", "gsk_***PLACEHOLDER***")

FIELD_KEYWORDS = {
    "NLP": ["language model", "llm", "transformer", "rag", "embedding",
            "text", "tokenizer", "prompt", "finetuning"],
    "CV": ["image", "vision", "object detection", "segmentation",
           "yolo", "diffusion", "gan", "depth estimation"],
    "RL": ["reinforcement learning", "rlhf", "policy gradient",
           "reward model", "agent", "mcts"],
    "음성/음악": ["speech", "audio", "tts", "asr", "voice",
                  "music", "speaker", "whisper"],
    "로봇": ["robot", "manipulation", "locomotion", "embodied",
             "grasp", "robotics", "drone"],
    "통계": ["statistics", "bayesian", "monte carlo",
             "hypothesis", "stochastic", "regression"]
}


def detect_field(title, abstract):
    text = (title + " " + abstract).lower()
    scores = {}
    for field, keywords in FIELD_KEYWORDS.items():
        s = sum(1 for kw in keywords if kw in text)
        if s > 0:
            scores[field] = s
    return max(scores, key=scores.get) if scores else "AI/ML"


def fetch_arxiv_papers(query="cat:cs.AI", max_results=3):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": query, "start": 0, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"arxiv err [{query}]: {e}")
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = re.sub(r"\s+", " ", entry.find("atom:title", ns).text.strip().replace("\n", " "))
        url_p = entry.find("atom:id", ns).text.strip()
        summary = re.sub(r"\s+", " ", entry.find("atom:summary", ns).text.strip().replace("\n", " "))[:1500]
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns)][:5]
        arxiv_id = url_p.split("/")[-1]
        papers.append({"id": arxiv_id, "title": title, "summary": summary,
                       "authors": authors, "url": url_p})
    return papers


def summarize(title, abstract):
    import requests
    prompt = (
        "Task: Translate an English AI paper into Korean summary.\n\n"
        "=== EXPECTED OUTPUT (write ONLY this, nothing else) ===\n"
        "한국어 제목: <Korean translation of title under 80 characters>\n"
        "한줄요약: <Korean one-line summary under 50 characters>\n\n"
        "=== INPUT ===\n"
        f"English title: {title}\n\nEnglish abstract: {abstract[:1200]}\n\n"
        "=== YOUR OUTPUT ==="
    )
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GK}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are a precise Korean translator. Write ONLY the format requested."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2, "max_tokens": 300,
            }, timeout=120)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if "choices" in data:
            text = data["choices"][0]["message"]["content"]
            return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    except Exception as e:
        print(f"  err: {e}")
    return None


def parse_summary(text, english_title=""):
    ko_title, summary = "", ""
    if not text:
        return english_title, "논문 원문을 확인하여 핵심 아이디어를 파악하세요."
    for line in text.split("\n"):
        line = line.strip()
        m = re.match(r"^[\s*]*한국어\s*제목\s*[:：]\s*(.+)$", line)
        if m:
            ko_title = m.group(1).strip().strip('"').strip("'").lstrip('**').rstrip('**')
            continue
        m = re.match(r"^[\s*]*한줄요약\s*[:：]\s*(.+)$", line)
        if m:
            summary = m.group(1).strip().strip('"').strip("'").lstrip('**').rstrip('**')
            continue
    if not ko_title or len(ko_title) < 3:
        ko_title = english_title
    if not summary or len(summary) < 5:
        summary = "논문 원문으로 핵심 아이디어를 확인하세요."
    return ko_title, summary


def make_post(paper, today_str):
    field = detect_field(paper["title"], paper["summary"])
    ai = summarize(paper["title"], paper["summary"])
    ko_title, summary = parse_summary(ai, paper["title"])

    return f"""---
layout: post
title: "{ko_title[:200]}"
date: {today_str} 09:00:00 +0900
categories: [ai]
tags: [arxiv, {field}, {paper["id"]}]
arxiv_id: "{paper["id"]}"
field: "{field}"
---

{summary}

<!-- more -->

*분야: {field}*

[원문 보러가기 →]({paper["url"]})
"""


def generate_field_pages():
    """각 분야별 Jekyll 페이지 자동 생성"""
    fields = [
        ("AI/ML",    "🤖 AI/ML",          "ai-ml"),
        ("CV",       "👁 Computer Vision","cv"),
        ("NLP",      "📝 NLP",            "nlp"),
        ("RL",       "🎮 Reinforcement",   "rl"),
        ("음성/음악",  "🎵 음성/음악",       "audio"),
        ("로봇",      "🦾 로봇",            "robotics"),
        ("통계",      "📊 통계",            "statistics"),
    ]

    for field_name, label, safe in fields:
        page = f"""---
layout: null
permalink: /field/{safe}/
---
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{label} — AI 논문 한 줄</title>
  <link rel="stylesheet" href="{{ '/assets/style.css' | relative_url }}">
</head>
<body>

<header class="site-header">
  <h1>{label}</h1>
  <p>이 분야의 최신 논문을 한국어 한 줄로 정리합니다</p>
  <nav class="field-tabs">
    <a class="field-tab" href="{{ '/' | relative_url }}">🏠 전체</a>
  </nav>
</header>

<div class="wrap">
  <h2 class="date-group">📚 {field_name} 논문</h2>
  <div class="cards">
    {{% assign page_field = '{field_name}' %}}
    {{% assign found = 0 %}}
    {{% for post in site.posts %}}
      {{% if post.field == page_field %}}
        <a class="card" href="{{{{ post.url | relative_url }}}}">
          <h3>{{{{ post.title }}}}</h3>
          <p class="summary">{{{{ post.excerpt | strip_html | truncate: 130 }}}}</p>
          <div class="meta">
            <span class="tag">arXiv:{{{{ post.arxiv_id }}}}</span>
            <span>📄 {{{{ post.date | date: "%Y-%m-%d" }}}}</span>
          </div>
        </a>
        {{% assign found = 1 %}}
      {{% endif %}}
    {{% endfor %}}
    {{% if found == 0 %}}
      <p style="text-align:center; color:#888; padding:40px 0;">
        아직 등록된 논문이 없습니다.
      </p>
    {{% endif %}}
  </div>
</div>

</body>
</html>
"""
        out_path = os.path.join(BLOG_DIR, f"field-{safe}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  📄 페이지 생성: field-{safe}.html")


def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    print("===== 분야 페이지 생성 =====")
    generate_field_pages()

    print("\n===== 논문 수집 =====")
    queries = [("cat:cs.AI", 3), ("cat:cs.LG", 3),
               ("cat:cs.CV", 2), ("cat:cs.CL", 2)]
    all_papers = []
    for q, n in queries:
        papers = fetch_arxiv_papers(q, max_results=n)
        all_papers.extend(papers)
        time.sleep(2)

    seen, unique = set(), []
    for p in all_papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    today_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    success = 0
    for paper in unique[:8]:
        filename = f"{today_str}-{paper['id'].replace('.', '-')}.md"
        out_path = os.path.join(POSTS_DIR, filename)
        print(f"  → {paper['id']}: {paper['title'][:60]}")
        post = make_post(paper, today_str)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(post)
        success += 1
        time.sleep(15)

    print(f"\n완료: {success}건 + 분야 페이지 7건")


if __name__ == "__main__":
    main()
