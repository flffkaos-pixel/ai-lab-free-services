#!/usr/bin/env python3
"""
arXiv -> 한국어 요약 -> Jekyll 블로그 + 분야별 페이지 자동 생성
v3: YAML 이스케이프 보강, 제목/요약 fallback 강화
"""

import os, json, re, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "blog", "_posts")
BLOG_DIR = os.path.join(ROOT, "blog")
GK = os.environ.get("GROQ_API_KEY", "gsk_***PLACEHOLDER***")

CATEGORY_MAP = {
    "cs.AI":   "AI/ML",
    "cs.LG":   "AI/ML",
    "cs.CL":   "NLP",
    "cs.CV":   "CV",
    "cs.RO":   "로봇",
    "cs.SD":   "음성/음악",
    "eess.AS": "음성/음악",
    "stat.ML": "통계",
    "stat.AP": "통계",
    "stat.CO": "통계",
    "cs.IR":   "NLP",
    "cs.NE":   "AI/ML",
    "cs.DC":   "AI/ML",
}

KEYWORD_BACKUP = {
    "NLP":      ["language model", "llm", "transformer", "rag", "embedding",
                 "tokenizer", "prompt", "finetuning", "nlp", "text generation"],
    "CV":       ["image", "vision", "object detection", "segmentation",
                 "yolo", "diffusion", "gan ", "depth estimation", "video"],
    "RL":       ["reinforcement learning", "rlhf", "policy gradient",
                 "reward model", "agent", "mcts", "markov decision"],
    "음성/음악":  ["speech", "audio", "tts", "asr", "voice",
                  "music", "speaker", "whisper", "sound"],
    "로봇":      ["robot", "manipulation", "locomotion", "embodied",
                 "grasp", "robotics", "drone"],
    "통계":      ["statistics", "bayesian", "monte carlo",
                 "hypothesis", "stochastic", "regression"],
}


def escape_yaml(s):
    """YAML double-quoted scalar escaping"""
    if not s:
        return ""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")


def detect_field(paper):
    for cat in paper.get("categories", []):
        if cat in CATEGORY_MAP:
            return CATEGORY_MAP[cat]
    text = (paper["title"] + " " + paper["summary"]).lower()
    scores = {}
    for field, kws in KEYWORD_BACKUP.items():
        s = sum(1 for kw in kws if kw in text)
        if s > 0:
            scores[field] = s
    if scores:
        return max(scores, key=scores.get)
    return "AI/ML"


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
        cats = []
        for c in entry.findall("atom:category", ns):
            term = c.attrib.get("term")
            if term:
                cats.append(term)
        papers.append({"id": arxiv_id, "title": title, "summary": summary,
                       "authors": authors, "url": url_p, "categories": cats})
    return papers


def summarize(title, abstract):
    import requests
    prompt = (
        "Task: Read an English AI paper and write a Korean translation of the title plus a ONE-LINE summary.\n\n"
        "=== OUTPUT FORMAT (write ONLY these 2 lines, nothing else) ===\n"
        "제목: <Korean title, natural and concise, under 80 chars>\n"
        "요약: <ONE sentence that includes the SPECIFIC CORE FINDING or RESULT. Use numbers/percentages if available.>\n\n"
        "=== CRITICAL RULES ===\n"
        "- The 요약 must describe the paper's KEY RESULT, not the method or background\n"
        "- Good: 'CoT 프롬프트를 적용해 수학 추론 능력을 기존 대비 23% 향상'\n"
        "- Good: '단 7B 모델이 GPT-4 수준의 수학 문제를 풀어내는 Few-shot 학습 기법 제안'\n"
        "- Bad: '이 논문은 대규모 언어 모델의 추론 능력을 향상시키는 방법을 제안합니다'\n"
        "- Include concrete numbers (accuracy %, BLEU score, parameters) if present in abstract\n"
        "- 요약 length: 30~70 characters (Korean)\n\n"
        "=== INPUT ===\n"
        f"English title: {title}\n\n"
        f"English abstract: {abstract[:1200]}\n\n"
        "=== OUTPUT (2 lines only) ==="
    )
    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GK}", "Content-Type": "application/json"},
            json={
                "model": "qwen/qwen3-32b",
                "messages": [
                    {"role": "system", "content": "You summarize AI research papers. Output EXACTLY 2 lines, no extra text:\nLine 1: 제목: <Korean title>\nLine 2: 요약: <Key result with numbers (e.g. '정확도 89.2% 달성', '기존 대비 23% 향상'). No method descriptions.>\nBad example: '이 논문은 LLM의 성능을 개선한다' (no numbers, vague)\nGood example: 'CoT 프롬프트로 수학 추론 능력 23% 향상' (specific result)"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 300,
            },
            timeout=300,
        )
        if resp.status_code != 200:
            print(f"  groq err: HTTP {resp.status_code} — body: {resp.text[:200]}")
            return None
        data = resp.json()
        if "choices" in data:
            text = data["choices"][0]["message"]["content"]
            text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
            return text.strip()
    except Exception as e:
        print(f"  err: {e}")
    return None


def parse_summary(text, english_title=""):
    ko_title, summary = "", ""
    if not text:
        return english_title, "arXiv 원문 초록을 확인하여 핵심 아이디어를 파악하세요."
    lines = [l.strip() for l in text.split("\n") if l.strip() and not l.strip().startswith("#")]
    for line in lines:
        m = re.match(r"^[*\s\-–]*제목\s*[:：]\s*(.+?)\s*[*]?$", line)
        if m:
            ko_title = m.group(1).strip().strip('"').strip("'").lstrip('**').rstrip('**')
            continue
        m = re.match(r"^[*\s\-–]*요약\s*[:：]\s*(.+?)\s*[*]?$", line)
        if m:
            summary = m.group(1).strip().strip('"').strip("'").lstrip('**').rstrip('**')
            continue
    if not ko_title or len(ko_title) < 3:
        ko_title = english_title
    if not summary or len(summary) < 5:
        summary = "arXiv 원문 초록을 확인하여 핵심 아이디어를 파악하세요."
    return ko_title, summary


def make_post(paper, today_str):
    field = detect_field(paper)
    ai = summarize(paper["title"], paper["summary"])
    ko_title, summary = parse_summary(ai, paper["title"])

    # 절대 빈 제목 방지
    if not ko_title or not ko_title.strip():
        ko_title = paper["title"][:200]
    if not summary or not summary.strip():
        summary = "arXiv 원문 초록을 확인하여 핵심 아이디어를 파악하세요."

    return (
        "---\n"
        "layout: post\n"
        f"title: \"{escape_yaml(ko_title[:200])}\"\n"
        f"date: {today_str} 09:00:00 +0900\n"
        f"categories: [{escape_yaml(field)}]\n"
        f"tags: [{escape_yaml(field)}, arxiv, {escape_yaml(paper['id'])}]\n"
        f"arxiv_id: \"{escape_yaml(paper['id'])}\"\n"
        f"field: \"{escape_yaml(field)}\"\n"
        f"summary: \"{escape_yaml(summary)}\"\n"
        "---\n"
        f"<p><strong>authors:</strong> {escape_yaml(', '.join(paper['authors']))}</p>\n"
        f"<p><strong>한 줄 요약:</strong> {escape_yaml(summary)}</p>\n"
    )


FIELD_DEFS = [
    ("AI/ML",   "🤖 AI/ML",            "ai-ml",      1),
    ("CV",      "👁 Computer Vision",  "cv",         2),
    ("NLP",     "📝 NLP",              "nlp",        3),
    ("RL",      "🎮 Reinforcement",    "rl",         4),
    ("음성/음악", "🎵 음성/음악",         "audio",      5),
    ("로봇",     "🦾 로봇",              "robotics",   6),
    ("통계",     "📊 통계",              "statistics", 7),
]


def generate_field_pages():
    tabs_html = []
    for field_name, label, safe, _ in FIELD_DEFS:
        tabs_html.append(f'<a class="field-tab" href="{{{{ \'/field/{safe}/\' | relative_url }}}}">{label}</a>')
    tabs_block = "\n    ".join(tabs_html)

    for field_name, label, safe, _ in FIELD_DEFS:
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
    {tabs_block}
  </nav>
</header>

<div class="wrap">
  <h2 class="date-group">📚 {field_name} 논문</h2>
  <div class="cards">
    {{{{%- assign found = 0 -%}}}}
    {{{{%- for post in site.posts -%}}}}
      {{{{%- if post.field == "{field_name}" -%}}}}
        <a class="card" href="{{{{{{ post.url | relative_url }}}}}}">
          <h3>{{{{{{ post.title }}}}}}</h3>
          <p class="summary">{{{{{{ post.excerpt | strip_html | truncate: 130 }}}}}}</p>
          <div class="meta">
            <span class="tag">arXiv:{{{{{{ post.arxiv_id }}}}}}</span>
            <span>📄 {{{{ post.date | date: "%Y-%m-%d" }}}}</span>
            <span>🏷 {{{{ post.field }}}}</span>
          </div>
        </a>
        {{{{%- assign found = 1 -%}}}}
      {{{{%- endif -%}}}}
    {{{{%- endfor -%}}}}
    {{{{%- if found == 0 -%}}}}
      <p style="text-align:center; color:#888; padding:40px 0;">
        아직 등록된 논문이 없습니다.
      </p>
    {{{{%- endif -%}}}}
  </div>
</div>

</body>
</html>
"""
        out_path = os.path.join(BLOG_DIR, f"field-{safe}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"  📄 페이지 생성: field-{safe}.html")


def load_existing_arxiv_ids():
    """기존 포스트에서 이미 처리된 arXiv ID 목록 반환"""
    existing = set()
    if not os.path.isdir(POSTS_DIR):
        return existing
    for fname in os.listdir(POSTS_DIR):
        if not fname.endswith(".md"):
            continue
        m = re.search(r'(\d{4}\.\d{4,5}v\d+)', fname)
        if m:
            existing.add(m.group(1))
    return existing


def main():
    os.makedirs(POSTS_DIR, exist_ok=True)
    print("===== 분야 페이지 생성 =====")
    generate_field_pages()

    print("\n===== 논문 수집 =====")
    queries = [("cat:cs.LG", 2),
               ("cat:cs.CL", 2),
               ("cat:cs.CV", 2),
               ("cat:cs.RO", 1),
               ("cat:cs.AI", 1),
               ]
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

    # 이미 존재하는 arXiv ID는 건너뛰기 (중복 방지)
    existing_ids = load_existing_arxiv_ids()
    today_str = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    success = 0
    for paper in unique[:8]:
        if paper["id"] in existing_ids:
            print(f"  ↩ {paper['id']}: 이미 기존 포스트에 존재, 건너뜀")
            continue
        filename = f"{today_str}-{paper['id'].replace('.', '-')}.md"
        out_path = os.path.join(POSTS_DIR, filename)
        if os.path.exists(out_path):
            print(f"  ↩ {paper['id']}: 이미 존재, 건너뜀")
            success += 1
            continue
        print(f"  → {paper['id']} [{detect_field(paper)}]: {paper['title'][:60]}")
        post = make_post(paper, today_str)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(post)
        success += 1
        time.sleep(15)

    print(f"\n완료: {success}건 + 분야 페이지 {len(FIELD_DEFS)}건")


if __name__ == "__main__":
    main()
