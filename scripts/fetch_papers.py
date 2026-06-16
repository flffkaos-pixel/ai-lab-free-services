#!/usr/bin/env python3
"""
arXiv에서 AI 분야 최신 논문 자동 수집 → 한국어 요약 → Jekyll 블로그 포스트
매일 GitHub Actions cron으로 실행
"""

import os, json, re, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog", "_posts")
GK = os.environ.get("GROQ_API_KEY", "gsk_***PLACEHOLDER***")

# 분야 키워드 → 태그 매핑
FIELD_KEYWORDS = {
    "NLP": ["language model", "llm", "transformer", "rag", "embedding",
            "text", "tokenizer", "prompt", "finetuning", "few-shot",
            "translation", "chatbot", "dialogue", "summarization", "question answering"],
    "CV":  ["image", "vision", "object detection", "segmentation",
            "yolo", "diffusion", "gan", "depth estimation", "pose estimation",
            "stable diffusion", "image generation", "video generation", "3d"],
    "RL":  ["reinforcement learning", "rlhf", "policy gradient", "q-learning",
            "reward model", "markov", "agent", "mcts", "monte carlo"],
    "음성/음악": ["speech", "audio", "tts", "asr", "voice", "music",
                  "speaker", "whisper", "wav2vec"],
    "로봇": ["robot", "manipulation", "locomotion", "embodied", "grasp",
             "robotics", "drone", "quadruped"],
    "통계": ["statistics", "bayesian", "monte carlo", "p-value", "hypothesis",
             "stochastic", "regression", "classification"]
}


def detect_field(title, abstract):
    """논문 분야 자동 분류"""
    text = (title + " " + abstract).lower()
    scores = {}
    for field, keywords in FIELD_KEYWORDS.items():
        s = sum(1 for kw in keywords if kw in text)
        if s > 0:
            scores[field] = s
    if not scores:
        return "AI/ML"
    return max(scores, key=scores.get)


def fetch_arxiv_papers(query="cat:cs.AI", max_results=3):
    """arXiv API에서 최신 논문 가져오기"""
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
        print(f"arxiv err [{query}]: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
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


def summarize(title, abstract):
    """Groq API로 한국어 1줄 요약 생성"""
    import requests
    prompt = f"""You will translate an AI paper into Korean. Output in EXACTLY this format and nothing else:

한국어 제목: <Korean title>
한줄요약: <30자 이내 한국어 요약>

Do NOT include ANY other sections. No "주요 기여", no "적용 분야", no explanation.

English title: {title}

English abstract: {abstract[:1200]}"""
    try:
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GK}", "Content-Type": "application/json"},
            json={
                "model": "qwen/qwen3-32b",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 400
            },
            timeout=60)
        data = resp.json()
        if "choices" in data:
            return data["choices"][0]["message"]["content"]
    except Exception as as_err:
        print(f"  summarize err: {as_err}")
    return None


def parse_summary(text, english_title=""):
    """'한국어 제목:' / '한줄요약:' 라인 파싱"""
    ko_title = ""
    summary = ""
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("한국어 제목:") or line.startswith("한국어 제목 "):
            ko_title = line.split(":", 1)[-1].strip()
        elif line.startswith("한줄요약:") or line.startswith("한줄요약 "):
            summary = line.split(":", 1)[-1].strip()
        elif line.startswith("**한국어 제목**:") or "**한줄요약**" in line:
            cleaned = line.replace("**", "").split(":", 1)[-1].strip()
            if "한줄요약" in cleaned[:8]:
                summary = cleaned.replace("한줄요약", "").strip()
            else:
                ko_title = cleaned.replace("한국어 제목", "").strip()

    if not ko_title or len(ko_title) < 3:
        ko_title = english_title
    if not summary or len(summary) < 5:
        summary = "논문 원문을 확인하여 핵심 아이디어를 파악하세요."
    return ko_title, summary


def make_post(paper, today_str):
    """마크다운 블로그 포스트 생성"""
    field = detect_field(paper["title"], paper["summary"])

    ai_summary = summarize(paper["title"], paper["summary"])
    if ai_summary:
        ko_title, summary = parse_summary(ai_summary, paper["title"])
    else:
        ko_title, summary = paper["title"], "AI 요약 생성 실패"

    # excerpt는 홈페이지 카드 미리보기에 표시
    excerpt = summary

    front_matter = f"""---
layout: post
title: "{ko_title[:200]}"
date: {today_str} 09:00:00 +0900
categories: [ai]
tags: [arxiv, {field}, {paper["id"]}]
arxiv_id: "{paper["id"]}"
field: "{field}"
excerpt: "{excerpt[:200]}"
---

{summary} <!-- more -->

[원문 보러가기 →]({paper["url"]})
"""
    return front_matter, excerpt


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # 분야 다양화: arXiv 주요 카테고리 6개에서 수집
    queries = [
        ("cat:cs.AI", 3),   # AI
        ("cat:cs.LG", 3),   # ML
        ("cat:cs.CV", 2),   # CV
        ("cat:cs.CL", 2),   # NLP
    ]

    all_papers = []
    for q, n in queries:
        papers = fetch_arxiv_papers(q, max_results=n)
        all_papers.extend(papers)
        time.sleep(2)  # arXiv 매너

    # 중복 제거
    seen = set()
    unique = []
    for p in all_papers:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    today_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    success = 0

    for paper in unique[:8]:
        filename = f"{today_str}-{paper['id'].replace('.', '-')}.md"
        out_path = os.path.join(OUT_DIR, filename)
        print(f"  → {paper['id']}: {paper['title'][:70]}")
        post, _ = make_post(paper, today_str)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(post)
        print(f"    ✅ 저장")
        success += 1
        time.sleep(15)  # Groq TPM 제한 대응

    print(f"\n완료: {success}건")


if __name__ == "__main__":
    main()
