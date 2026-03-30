#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from ai import chat


BASE_DIR = Path(__file__).resolve().parents[1]
TESTS_DIR = BASE_DIR / "tests"


def list_pdfs() -> list[Path]:
    if not TESTS_DIR.exists():
        return []
    return sorted(TESTS_DIR.glob("*.pdf"), key=lambda p: p.name.lower())


def resolve_pdf(filename: str) -> Path:
    pdf_path = (TESTS_DIR / filename).resolve()
    if TESTS_DIR.resolve() not in pdf_path.parents:
        raise ValueError("Invalid file path")
    if not pdf_path.exists() or pdf_path.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"PDF not found in tests/: {filename}")
    return pdf_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Quick CLI for local syllabus parsing tests")
    parser.add_argument("--list", action="store_true", help="List available PDFs in tests/")
    parser.add_argument("--file", type=str, help="PDF filename from tests/ to analyze")
    parser.add_argument("--out", type=str, help="Optional output JSON file path")
    args = parser.parse_args()

    if args.list:
        files = list_pdfs()
        if not files:
            print("No PDF files found in tests/")
            return 0
        print("Available PDFs:")
        for pdf in files:
            print(f"- {pdf.name}")
        return 0

    if not args.file:
        parser.error("Provide --file <name.pdf> or use --list")

    pdf_path = resolve_pdf(args.file)
    result_json = chat(str(pdf_path))

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(result_json, encoding="utf-8")
        print(f"Saved output to {out_path}")
    else:
        parsed = json.loads(result_json)
        print(json.dumps(parsed, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
