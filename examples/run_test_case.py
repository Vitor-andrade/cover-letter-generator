"""Run a saved test case end-to-end to eyeball generation quality.

Exercises the real pipeline — ingestion + prompt + the configured AI provider
(``CLG_AI_PROVIDER`` and its key from ``.env``) — without touching the database.
Handy for iterating on the prompt without clicking through the UI every time.

Usage:
    uv run python examples/run_test_case.py --cv /path/to/cv.pdf
    uv run python examples/run_test_case.py --cv cv.pdf --name "Vitor Cavalcante"
    uv run python examples/run_test_case.py --cv cv.pdf --case proxify-senior-fullstack
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from clg.core.generation.prompt import build_generation_prompt
from clg.core.ingestion.parse import extract_upload
from clg.core.providers.base import CompletionParams
from clg.core.providers.registry import build_provider, resolve_model

EXAMPLES_DIR = Path(__file__).parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cv", required=True, help="Path to a CV in PDF or DOCX format.")
    parser.add_argument(
        "--case",
        default="proxify-senior-fullstack",
        help="Test-case file in examples/ (without the .json extension).",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Candidate name for the signature; defaults to the name found in the CV.",
    )
    parser.add_argument("--language", default="en", help="Letter language code (e.g. en, pt).")
    args = parser.parse_args()

    case = json.loads((EXAMPLES_DIR / f"{args.case}.json").read_text(encoding="utf-8"))
    job_description = (EXAMPLES_DIR / case["job_description_file"]).read_text(encoding="utf-8")

    cv_path = Path(args.cv)
    extracted = extract_upload(cv_path.name, cv_path.read_bytes())
    if extracted.low_confidence:
        print("WARNING: little text extracted from the CV — check the file.\n")

    prompt = build_generation_prompt(
        background_text=extracted.text,
        job_title=case["job_title"],
        company=case.get("company"),
        job_description=job_description,
        language=args.language,
        candidate_name=args.name,
    )

    provider = build_provider()
    model = resolve_model(provider.name)
    print(f"# Provider: {provider.name} · model: {model} · case: {args.case}\n")
    print(provider.complete(prompt, CompletionParams(model=model, language=args.language)))


if __name__ == "__main__":
    main()
