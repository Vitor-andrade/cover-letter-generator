# Test cases

Saved job postings to make manual testing repeatable. Each case is a small JSON
file plus a `.jd.txt` holding the raw job description.

| Case | Job title | Company |
|------|-----------|---------|
| `proxify-senior-fullstack` | Senior fullstack developer ( Python ) | Proxify |

## Option A — in the app (UI)

1. Start the app: `uv run clg`.
2. Enter your name and upload (or paste) your CV.
3. Copy **Job title** and **Company** from the case's `.json`, and paste the
   contents of its `.jd.txt` into **Job description**.
4. Pick the language and click **Generate cover letter**.

## Option B — from the terminal (no UI, no database)

Runs ingestion → prompt → the configured AI provider and prints the letter.
Uses `CLG_AI_PROVIDER` and the key from your `.env`.

```bash
uv run python examples/run_test_case.py --cv /path/to/your_cv.pdf
# pick a different case or set the signature name explicitly:
uv run python examples/run_test_case.py --cv cv.pdf --case proxify-senior-fullstack --name "Your Name"
```

## Adding a new case

1. Create `examples/<slug>.jd.txt` with the raw job description.
2. Create `examples/<slug>.json`:
   ```json
   { "job_title": "...", "company": "...", "job_description_file": "<slug>.jd.txt" }
   ```
3. Run it with `--case <slug>`.
