# API Review Feedback Chatmode - Evaluation Framework

Automated testing framework for the API Review Feedback chatmode that validates TypeSpec code generation from API review feedback.

## Requirements

- **Python 3**
- **Node.js** with TypeSpec compiler installed globally:

  ```bash
  npm install -g @typespec/compiler
  ```

- **API credentials** (one of):
  - `OPENAI_API_KEY` - OpenAI API key
  - `AZURE_OPENAI_ENDPOINT` + `AZURE_OPENAI_API_KEY` - Azure OpenAI
  - `AZURE_OPENAI_ENDPOINT` + Azure AD auth via `az login`

## Quick Start

```bash
# From repo root
npm ci  # Install TypeSpec dependencies

# From this directory
cd .github/chatmodes/api-review-feedback/evals/
pip install -r requirements.txt

# Set up environment (Azure OpenAI or OpenAI API key)
cp .env.example .env
# Edit .env with your credentials

# Run tests
python run.py --scenario test-client-namespace
```

## How It Works

1. **Aggregates feedback** - Combines all feedback items from `test_cases.json` into one conversation
2. **Calls GPT-4o** - Sends feedback + TypeSpec context to the chatmode
3. **Extracts output** - Parses the generated `client.tsp` from the response
4. **Compiles** - Runs `tsp compile ./client.tsp --no-emit` to validate syntax
5. **Validates** - Checks for required decorators, imports, and compilation success
6. **Reports results** - Generates pass/fail report

## Test Modes

### Fast Mode (Default)

Single LLM call, no checkpoint validation. Use for quick iterations.

```bash
python run.py --scenario test-client-namespace
```

### Eval Mode

Runs 5+ checkpoints to validate model reasoning at each step. Use for detailed evaluation.

```bash
python run.py --scenario test-client-namespace --eval-mode
```

## Output Structure

```text
tests/test-name/results/
├── raw/
│   ├── system_prompt.md          # Chatmode system prompt
│   ├── user_prompt.md            # Full user message with context
│   ├── response.txt              # Complete LLM response
│   ├── conversation.log.jsonl    # Full conversation history
│   └── checkpoints/              # Checkpoint JSONs (eval mode only)
│       ├── CHECKPOINT_1.json
│       └── ...
├── extracted/
│   └── client.tsp                # Extracted TypeSpec from response
└── build/
    ├── compile.txt               # Compilation output
    └── temp_spec/                # Temp copy of spec with injected client.tsp
```

## Creating Tests

1. Create a test scenario folder: `tests/test-my-feature/`

2. Add `test_cases.json`:

   ```json
   [
     {
       "feedback": "Rename the property foo to bar in MyModel",
       "language": "all",
       "tags": ["rename"]
     }
   ]
   ```

3. Add specification files: `tests/test-my-feature/specification/`
   - These may or may not include an existing `client.tsp` file.

4. Add the expected `client.tsp` output: `tests/test-my-feature/expected/client.tsp`
   - If any lines in the `client.tsp` aren't required, add a comment `// OPTIONAL` at the end of the line.

5. Run: `python run.py --scenario test-my-feature`

## Validation

Tests validate:

- ✅ TypeSpec compilation success
- ✅ Required decorators present (extracted from `expected/client.tsp`)
- ✅ Required imports and using statements
- ✅ No forbidden patterns

See test scenarios in `tests/` for examples.
