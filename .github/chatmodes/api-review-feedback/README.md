# API Review Feedback Chatmode Evaluations

Guide for running evaluation tests of the API Review Feedback chatmode.

## Quick Start

```bash
# In repo root (ensure deps installed)
npm ci                     # installs TypeSpec-related deps (tsp-client etc.)
cd .github/chatmodes/api-review-feedback/evals/
pip install -r requirements.txt

# Run all evaluation scenarios
python run.py
```

## Requirements

- Python 3
- Node.js + `@typespec/compiler` (install globally if not already):

  ```bash
  npm install -g @typespec/compiler
  ```
  - or 
Create a local `.env` with the following environment variables:

  ```bash
  OPENAI_API_KEY=<openai-api-key>
  # OR
  AZURE_OPENAI_ENDPOINT=<azure-openai-endpoint>
  AZURE_OPENAI_API_KEY=<azure-openai-key> # OR log in via `az login` for AAD auth
  ```

## Running Tests

Run all scenarios:

```bash
python run.py
```

Filter by scenario folder name (e.g. `test-renames-basic`):

```bash
python run.py --scenario renames-basic
```

Report file (defaults to `tests/test_report.md`):

```bash
python run.py --report custom_report.md
```

Exit code is non‑zero if any test fails (CI friendly).

## Test Layout

```text
api-review-feedback/
  evals/
    tests/
      test-<scenario>/
        specification/           # Minimal TypeSpec source context
        expected/client.tsp      # Expected client.tsp file
        test_cases.json          # Array of test case objects
        results/<testcase>/      # Per‑test artifacts
          raw/                   # Raw model response + prompts
          extracted/             # Extracted client.tsp
          build/                 # compile.txt with stdout/err (TypeSpec compile output)
          diff/                  # diff of output to expected
```

## Artifacts

Per test case you get:

- `raw/response.txt` – untouched model output
- `raw/user_prompt.md` / `system_prompt.md` – test cases + chatmode prompt
- `extracted/client.tsp` – full client.tsp in response
- `build/compile.txt` – compiler stdout/stderr
- `diff/unified.diff` – textual diff vs expected (when mismatch)

Aggregate summary lives in: `tests/test_report.md`.

## What Counts as Pass

1. Semantic match (imports/using/namespace/decorators) with expected `client.tsp`
2. Successful `tsp compile` in isolated temp workspace (client injected)
3. All `expected_decorators` (if listed in test case) present

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Missing decorators flagged | Adjust prompt or refine chatmode logic; harness looks for literal substrings. |
