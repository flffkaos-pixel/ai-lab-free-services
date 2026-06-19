#!/usr/bin/env python3
"""field 페이지 생성 — 일일논문과 동일한 date-grouped 구조"""
import os

BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog")

FIELD_DEFS = [
    ("AI/ML",   "🤖 AI/ML",            "ai-ml"),
    ("CV",      "👁 Computer Vision",  "cv"),
    ("NLP",     "📝 NLP",              "nlp"),
    ("RL",      "🎮 Reinforcement",    "rl"),
    ("음성/음악", "🎵 음성/음악",         "audio"),
    ("로봇",     "🦾 로봇",              "robotics"),
    ("통계",     "📊 통계",              "statistics"),
]

for field, label, slug in FIELD_DEFS:
    tmpl = (
        "---\n"
        "layout: default\n"
        "permalink: /field/" + slug + "/\n"
        "---\n\n"
        "<section class=\"intro\">\n"
        "  <p>" + label + " 분야에서 최신 논문을 <strong>한국어 한 줄 요약</strong>으로 정리합니다.</p>\n"
        "</section>\n\n"
        "<h2>" + label + " 논문</h2>\n\n"
        "<ul class=\"report-list\">\n"
        "{% assign filtered = site.posts | where: \"field\", \"" + field + "\" %}\n"
        "{% assign posts_by_date = filtered | group_by: \"date\" %}\n"
        "{% for date in posts_by_date limit: 30 %}\n"
        "  <li>\n"
        "    <div class=\"rl-head\">\n"
        "      <time>{{ date.name | date: \"%Y-%m-%d\" }}</time>\n"
        "      <span class=\"count-badge\">{{ date.items.size }}건</span>\n"
        "    </div>\n"
        "    <div class=\"rl-top3\">\n"
        "      <span class=\"rl-label\">논문</span>\n"
        "{% for post in date.items limit: 6 %}\n"
        "      <span class=\"t3-chip\"><b>{{ post.field }}</b>\n"
        "        <a href=\"{{ post.url | relative_url }}\">{{ post.title | truncate: 28 }}</a>\n"
        "      </span>\n"
        "{% endfor %}\n"
        "    </div>\n"
        "  </li>\n"
        "{% endfor %}\n"
        "</ul>\n\n"
        "{% if filtered.size == 0 %}\n"
        "<p style=\"text-align:center; color:var(--muted); padding:40px 0;\">\n"
        "  아직 등록된 논문이 없습니다.\n"
        "</p>\n"
        "{% endif %}\n"
    )
    path = os.path.join(BLOG_DIR, f"field-{slug}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(tmpl)
    print(f"  field-{slug}.html")

print("done")