"""
summarize.py — CLI wrapper around the analysis pipeline.

Usage:
    python summarize.py <input_file> [--output <output_pdf>]

For one-off testing without running the FastAPI server.
"""

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from pipeline import run_analysis
from extractor import extract_text
from renderer import render_to_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a document (.txt or .pdf) into actionable insights."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input file (.txt or .pdf).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output PDF path. Defaults to <input>_summary.pdf.",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or args.input.with_name(
        f"{args.input.stem}_summary.pdf"
    )

    print(f"Reading: {args.input}")
    try:
        content = extract_text(args.input)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracted {len(content)} characters. Sending to Gemini...")
    analysis = run_analysis(content)

    print(json.dumps(analysis.model_dump(), indent=2, ensure_ascii=False))

    render_to_pdf(analysis, output_path)
    print(f"\nPDF written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
