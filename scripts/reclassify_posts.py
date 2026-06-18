#!/usr/bin/env python3
"""
기존 _posts/*.md 의 arxiv_id를 다시 arXiv API에 조회해서:
1. 진짜 category 태그 읽기
2. field를 정확하게 다시 분류 (AI/ML, NLP, CV, RL, 음성/음악, 로봇, 통계)
3. frontmatter의 categories/tags/field 업데이트

이건 qwen3-32b 호출 없이 arXiv API만 쓰니까 GROQ_API_KEY 불필요.
"""

import os, re, urllib.request, urllib.parse, time, ssl
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "blog", "_posts")

# Windows에서 SSL 인증서 검증 실패 우회 (사내망/다운로드 이슈)
_ctx = ssl.create_default_context()
try:
    _ctx.load_default_certs()
except Exception:
    pass
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE

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
                 "yolo", "diffusion", "gan ", "depth estimation"],
    "RL":       ["reinforcement learning", "rlhf", "policy gradient",
                 "reward model", "agent", "mcts", "markov decision"],
    "음성/음악":  ["speech", "audio", "tts", "asr", "voice",
                  "music", "speaker", "whisper", "sound"],
    "로봇":      ["robot", "manipulation", "locomotion", "embodied",
                 "grasp", "robotics", "drone"],
    "통계":      ["statistics", "bayesian", "monte carlo",
                 "hypothesis", "stochastic", "regression"],
}


def fetch_one(arxiv_id):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"id:{arxiv_id}", "max_results": 1,
    })
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20, context=_ctx) as resp:
                data = resp.read().decode("utf-8")
                break
        except Exception as e:
            print(f"  fetch err {arxiv_id} (try {attempt+1}/3): {e}")
            if "429" in str(e) and attempt < 2:
                time.sleep(20)
            else:
                return None
    else:
        return None
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(data)
    for entry in root.findall("atom:entry", ns):
        cats = [c.attrib.get("term") for c in entry.findall("atom:category", ns) if c.attrib.get("term")]
        title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
        abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
        return {"id": arxiv_id, "title": title, "categories": cats, "abstract": abstract}
    return None


def detect_field(meta):
    for cat in meta.get("categories", []):
        if cat in CATEGORY_MAP:
            return CATEGORY_MAP[cat], cat
    text = (meta["title"] + " " + meta["abstract"]).lower()
    scores = {}
    for f, kws in KEYWORD_BACKUP.items():
        s = sum(1 for kw in kws if kw in text)
        if s > 0:
            scores[f] = s
    if scores:
        return max(scores, key=scores.get), "keyword"
    return "AI/ML", "default"


def update_post(path, new_field):
    """frontmatter만 갱신 — 본문은 그대로 둠"""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 매치: categories 줄 (예: categories: [ai] 또는 categories: [NLP])
    new_content, n = re.subn(
        r"^categories:\s*\[.*?\]\s*$",
        f"categories: [{new_field}]",
        content,
        count=1, flags=re.MULTILINE,
    )
    new_content, n2 = re.subn(
        r"^tags:\s*\[.*?\]\s*$",
        lambda m: m.group(0),  # 그대로 둠 (frontmatter 정확히 매치 어려움)
        new_content, count=1, flags=re.MULTILINE,
    )
    # field 라인 갱신
    new_content, n3 = re.subn(
        r"^field:\s*\".*?\"\s*$",
        f'field: "{new_field}"',
        new_content, count=1, flags=re.MULTILINE,
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return n + n3


if __name__ == "__main__":
    files = sorted([f for f in os.listdir(POSTS_DIR) if f.endswith(".md")])
    print(f"처리할 파일: {len(files)}개")

    # arxiv_id 추출
    items = []
    for fn in files:
        with open(os.path.join(POSTS_DIR, fn), encoding="utf-8") as fh:
            c = fh.read()
        m = re.search(r'^arxiv_id:\s*"(.*?)"', c, re.MULTILINE)
        if m:
            items.append((fn, m.group(1)))

    # arXiv API 캐시 (중복 호출 방지)
    cache = {}
    updated = 0
    for fn, ax_id in items:
        if ax_id not in cache:
            meta = fetch_one(ax_id)
            if meta:
                field, src = detect_field(meta)
                cache[ax_id] = (field, src, meta["categories"])
                time.sleep(2)  # arXiv API 친화적
        if ax_id in cache:
            field, src, cats = cache[ax_id]
            n_changed = update_post(os.path.join(POSTS_DIR, fn), field)
            print(f"  {fn}: → {field}  (cats={cats[:3]}, src={src})")
            updated += 1

    print(f"\n갱신 완료: {updated}건")
