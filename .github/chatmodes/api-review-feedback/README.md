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

- One of:
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

Tests use **semantic validation** (not exact file matching):

0. `namespace ClientCustomizations;` is present (always required)
1. Compilation success in isolated temp workspace (always required)
2. Required decorators present (with flexible path matching - handles both `Type` and `Namespace.Type`)
3. Required imports and using statements present
4. No forbidden patterns (e.g., old snake_case names)

### Test Format

Tests use **format-agnostic validation** that checks what the TypeSpec actually does, not how it's written.

**Recommended: Use `expected_renames` format**

```json
{
  "testcase": "example",
  "feedback": "Rename property X to Y in Python",
  "validation": {
    "expected_renames": {
      "python": {
        "AnswersOptions.confidenceScoreThreshold": "confidenceThreshold",
        "ShortAnswerOptions.confidenceScoreThreshold": "confidenceThreshold"
      }
    },
    "forbidden_patterns": ["old_snake_case_name"]
  }
}
```

**How it works:**

- Parses the generated `client.tsp` to extract ALL `@@clientName` decorators
- Normalizes paths (handles both `Model.property` and `Namespace.Model.property`)
- Validates: "Is property X renamed to Y in language Z?"
- **Format-agnostic**: doesn't care about whitespace, fully-qualified paths, file structure, etc.

#### Alternative: Extract from expected file (legacy)

Create `expected/client.tsp` and omit `expected_renames`:

```typespec
import "@azure-tools/typespec-client-generator-core";
using Azure.ClientGenerator.Core;

namespace ClientCustomizations;

@@clientName(Model.property, "newName", "python");
@@clientName(Model.anotherProperty, "anotherName", "python");  // OPTIONAL
```

Lines marked with `// OPTIONAL` are not validated.

**Notes**:

- `namespace ClientCustomizations;` and compilation success are always required (checked automatically)
- Decorator validation always allows fully-qualified namespace paths (e.g., `Namespace.Model.property`) by default.
- `language` field is optional and can be:
  - Omitted (for decorators without language parameter)
  - A single string: `"python"`
  - A list of strings: `["python", "java"]` (for multiple languages)
- Use `// OPTIONAL` comments in expected file to mark decorators that may or may not be generated

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Cannot find chatmode file | Ensure `api-review-feedback-smart.chatmode.md` exists at `.github/chatmodes/` root level. |
| Compilation schema error | The harness auto‑writes a minimal `tspconfig.yaml`; verify emit plugin spelling. |
| Empty `client.tsp` extracted | Model only emitted checkpoint JSON. (Multi‑turn orchestration active) |
| Test fails but output looks correct | Check validation rules: decorator may use fully-qualified paths vs short paths. Both are valid. |
