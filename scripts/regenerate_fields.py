#!/usr/bin/env python3
"""Regenerate all field pages using layout:default for main-site consistency."""
import os, re, sys

ROOT = os.path.expanduser("~/free-services")
POSTS_DIR = os.path.join(ROOT, "blog", "_posts")
BLOG_DIR = os.path.join(ROOT, "blog")

FIELD_DEFS = [
    ("AI/ML",   "AI/ML - AI \ub17c\ubb38 \ud55c \uc904",          "ai-ml"),
    ("CV",      "CV - AI \ub17c\ubb38 \ud55c \uc904",              "cv"),
    ("NLP",     "NLP - AI \ub17c\ubb38 \ud55c \uc904",             "nlp"),
    ("RL",      "RL - AI \ub17c\ubb38 \ud55c \uc904",              "rl"),
    ("\uc74c\uc131/\uc74c\uc545", "\uc74c\uc131/\uc74c\uc545 - AI \ub17c\ubb38 \ud55c \uc904",       "audio"),
    ("\ub85c\ubd07", "\ub85c\ubd07 - AI \ub17c\ubb38 \ud55c \uc904",            "robotics"),
    ("\ud1b5\uacc4", "\ud1b5\uacc4 - AI \ub17c\ubb38 \ud55c \uc904",            "statistics"),
]

# Load all posts
all_posts = []
for fname in os.listdir(POSTS_DIR):
    if not fname.endswith(".md"):
        continue
    fpath = os.path.join(POSTS_DIR, fname)
    with open(fpath, encoding="utf-8") as f:
        content = f.read()
    post = {"date": "", "title": "", "summary": "", "field": "", "id": ""}
    for line in content.split("\n"):
        if line.startswith("date:"):
            post["date"] = line.split(":")[1].strip().split()[0] if " " in line else line.split(":")[1].strip()
        elif line.startswith("title:"):
            post["title"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("summary:"):
            post["summary"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("field:"):
            post["field"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("arxiv_id:"):
            post["id"] = line.split(":", 1)[1].strip().strip('"')
    if post["field"] and post["id"]:
        all_posts.append(post)

print(f"Loaded {len(all_posts)} posts")

for field_name, title, safe in FIELD_DEFS:
    field_posts = [p for p in all_posts if p.get("field") == field_name]
    field_posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    field_posts = field_posts[:50]

    cards = []
    for p in field_posts:
        pid = p.get("id", "")
        pid_stub = pid.replace(".", "-")
        url = "/ai-lab-free-services/" + p.get('date', '').replace('-', '/') + "/" + pid_stub + "/"
        title2 = p.get("ko_title", p.get("title", "Untitled"))
        summary = p.get("summary", "")
        cards.append(
            '<a class="card" href="' + url + '">\n'
            + '          <h3>' + title2 + '</h3>\n'
            + '          <p class="summary">' + summary + '</p>\n'
            + '          <div class="meta">\n'
            + '            <span class="tag">arXiv:' + pid + '</span>\n'
            + '            <span>&#x1F4C4; ' + p.get('date', '') + '</span>\n'
            + '            <span>&#x1F3F7; ' + field_name + '</span>\n'
            + '          </div>\n'
            + '        </a>'
        )

    block = "\n".join(cards) if cards else (
        '<p style="text-align:center;color:#888;padding:40px 0;">\n'
        '  \uc544\uc9c1 \ub4f1\ub85d\ub41c \ub17c\ubb38\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.\n'
        '</p>'
    )

    page = ("---\n"
                + "layout: default\n"
                + "title: " + title + "\n"
                + "permalink: /field/" + safe + "/\n"
                + "---\n"
                + "\n"
            + '<div class="wrap">\n'
            + '  <h2 class="date-group">\U0001f4da ' + field_name + ' \ub17c\ubb38</h2>\n'
            + '  <div class="cards">\n'
            + block + "\n"
            + '  </div>\n'
            + '</div>\n')

    out_path = os.path.join(BLOG_DIR, "field-" + safe + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print("  field-" + safe + ".html")

print("Done. All field pages use layout:default - same header/nav as main site.")