#!/usr/bin/env python3
"""fetch_papers로 생성된 old MD의 푸터/format 정리 — 이미 카드 잘 보이게"""
import sys, os
# 단순 실행: 기존 8개 md 파일 다 읽어서 푸터 제거 + 다시 저장
# GitHub Actions에서만 실행됨

DIR = sys.argv[1] if len(sys.argv) > 1 else "_posts"
import re
count = 0
for fn in sorted(os.listdir(DIR)):
    if not fn.endswith('.md'): continue
    p = os.path.join(DIR, fn)
    with open(p, encoding='utf-8') as f:
        c = f.read()
    # 푸터 제거 (이미 v2에서는 푸터 없음)
    # 만약 *본 글은 Qwen3-32B이 arXiv에서...* 줄이 있으면 제거
    new = re.sub(r'\n\*본 글은.*?확인하세요\.\*', '', c, flags=re.DOTALL)
    if new != c:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new)
        count += 1
print(f"정리: {count}건")