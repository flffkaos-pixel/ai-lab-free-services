#!/usr/bin/env python3
"""field 페이지 생성 — layout: default 사용"""
import os

BLOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blog")

FIELD_DEFS = [
    ("AI/ML",   "🤖 AI/ML",            "ai-ml"),
    ("CV",      "👁 Computer Vision",  "cv"),
    ("NLP",     "📝 NLP",              "nlp"),
    ("RL",      "🎮 강화학습",          "rl"),
    ("음성/음악", "🎵 음성/음악",         "audio"),
    ("로봇",     "🦾 로봇",              "robotics"),
    ("통계",     "📊 통계",              "statistics"),
]

for field_name, label, safe in FIELD_DEFS:
    page = f"""---
layout: default
permalink: /field/{safe}/
title: {label} 분야
---

<h2>{label} 논문</h2>

<ul class="report-list">
  {{% assign found = 0 %}}
  {{% for post in site.posts %}}
    {{% if post.field == "{field_name}" %}}
      <li>
        <div class="rl-head">
          <time>{{{{ post.date | date: "%Y-%m-%d" }}}}</time>
          <a href="{{{{ post.url | relative_url }}}}">{{{{ post.title }}}}</a>
          <span class="field-tag">{{{{ post.field }}}}</span>
        </div>
        <p style="margin:6px 0 0; color:var(--muted); font-size:.88rem;">
          {{{{ post.excerpt | strip_html | truncate: 130 }}}}
        </p>
      </li>
      {{% assign found = 1 %}}
    {{% endif %}}
  {{% endfor %}}
  {{% if found == 0 %}}
    <li style="text-align:center; color:var(--faint); padding:40px;">
      아직 등록된 논문이 없습니다.
    </li>
  {{% endif %}}
</ul>
"""
    out_path = os.path.join(BLOG_DIR, f"field-{safe}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"  📄 field-{safe}.html")

print("✅ 완료")