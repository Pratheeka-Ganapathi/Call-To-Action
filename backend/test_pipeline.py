"""Quick standalone test of the two-stage pipeline."""

import json
from dotenv import load_dotenv

from pipeline import run_analysis


load_dotenv()

with open("sample_content.txt", encoding="utf-8") as f:
    content = f.read()

print(f"Input: {len(content)} characters")
print("Running stage 1 (Qwen) → stage 2 (Gemini)...")
print()

analysis = run_analysis(content)

print("=== FINAL ANALYSIS ===")
print(json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False))