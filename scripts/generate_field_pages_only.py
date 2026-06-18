#!/usr/bin/env python3
"""fetch_papers.py의 generate_field_pages()만 부분 실행 (GROQ 호출 없이)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

# GROQ 호출이 없는 부분만 실행되도록 fetch_papers 임포트 후 generate_field_pages() 호출
import importlib.util
spec = importlib.util.spec_from_file_location("fetch_papers", os.path.join(ROOT, "scripts", "fetch_papers.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.generate_field_pages()
