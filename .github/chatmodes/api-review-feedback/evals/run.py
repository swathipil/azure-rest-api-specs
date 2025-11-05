#!/usr/bin/env python3
"""
Enhanced evaluation runner for the API Review Feedback chatmode agent.
Supports new test structure with isolated scenarios and file-based validation.
"""

import os
import asyncio
import json
import argparse
import subprocess
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

try:
    import dotenv
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
except ImportError:
    print("Error: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Load environment variables (root .env plus chatmode-local .env if present)
dotenv.load_dotenv()  # default search upwards from CWD
chatmode_env = Path(__file__).parent.parent / ".env"
if chatmode_env.exists():
    dotenv.load_dotenv(dotenv_path=chatmode_env, override=True)

# Model configuration
MODEL = "gpt-4o"
API_VERSION = "2024-10-21"
CHATMODE_FILE_NAME = "api-review-feedback-smart.chatmode.md"
#CHATMODE_FILE_NAME = "api-review-feedback.chatmode.md"

class TypeSpecTestResult:
    """Result of a TypeSpec test case execution."""

    def __init__(self, testcase: str, success: bool, message: str,
                 generated_file: Optional[str] = None, expected_file: Optional[str] = None,
                 diff: Optional[str] = None, compilation_result: Optional[str] = None):
        self.testcase = testcase
        self.success = success
        self.message = message
        self.generated_file = generated_file
        self.expected_file = expected_file
        self.diff = diff
        self.compilation_result = compilation_result

class TypeSpecFileComparator:
    """Handles semantic validation of TypeSpec files."""

    @staticmethod
    def build_decorator_regex(decorator: str, target: str, args: List[str],
                              allow_fq: bool = True, languages: Optional[List[str]] = None) -> str:
        """Build regex that matches decorator with optional namespace qualification.

        Args:
            decorator: Decorator name (e.g., '@@clientName')
            target: Target path (e.g., 'AnswersOptions.confidenceScoreThreshold')
            args: List of string arguments (e.g., ['"confidenceThreshold"'])
            allow_fq: If True, allows any namespace prefix before target
            languages: Optional list of language parameters (e.g., ['python', 'java'])

        Returns:
            Compiled regex pattern that matches the decorator with flexible formatting
        """
        if allow_fq:
            # Extract the final component of the target path
            target_parts = target.split('.')
            # Allow optional namespace prefix: (Namespace.)*FinalComponent
            # Match any dotted path ending with our target
            escaped_parts = [re.escape(part) for part in target_parts]
            # Allow 0 or more namespace segments, then our path
            target_pattern = r'(?:[\w.]+\.)?' + r'\.'.join(escaped_parts)
        else:
            target_pattern = re.escape(target)

        # Build argument pattern with flexible whitespace
        arg_patterns = [re.escape(arg) if not arg.startswith('"') else re.escape(arg)
                       for arg in args]

        # Add language parameters if provided
        if languages:
            for lang in languages:
                arg_patterns.append(re.escape(f'"{lang}"'))

        args_str = r'\s*,\s*'.join(arg_patterns)

        # Final pattern: decorator(target, args) with flexible whitespace
        pattern = rf'{re.escape(decorator)}\s*\(\s*{target_pattern}\s*,\s*{args_str}\s*\)'
        return pattern

    @staticmethod
    def validate_decorator_semantic(content: str, decorator_spec: Dict[str, Any]) -> Tuple[bool, str]:
        """Semantically validate that a decorator exists in content.

        Handles:
        - Optional namespace qualification (Namespace.Type vs Type)
        - Whitespace variations
        - Argument formatting
        - Multiple languages or no language

        Args:
            content: TypeSpec file content
            decorator_spec: Dict with keys: decorator, target, new_name, language (optional, can be string or list)

        Returns:
            (success, error_message)
        """
        decorator = decorator_spec.get("decorator")
        target = decorator_spec.get("target")
        new_name = decorator_spec.get("new_name")
        language = decorator_spec.get("language")
        allow_fq = decorator_spec.get("allow_fq_target", True)

        if not all([decorator, target, new_name]):
            return False, "Invalid decorator spec: missing required fields"

        # Build arguments list
        args = [f'"{new_name}"']

        # Normalize language to list
        languages = None
        if language:
            if isinstance(language, str):
                languages = [language]
            elif isinstance(language, list):
                languages = language

        # Build and search for pattern
        pattern = TypeSpecFileComparator.build_decorator_regex(
            decorator, target, args, allow_fq, languages
        )

        match = re.search(pattern, content, re.MULTILINE)
        if match:
            return True, ""
        else:
            # Provide helpful error message
            expected = f'{decorator}({target}, "{new_name}"'
            if languages:
                for lang in languages:
                    expected += f', "{lang}"'
            expected += ')'
            return False, f"Missing or malformed: {expected}"

class TypeSpecChatmodeRunner:
    """Handles running the chatmode against test scenarios."""

    def __init__(self, eval_mode: bool = False):
        self.system_prompt = self._extract_chatmode_system_prompt()
        self.checkpoints = self._discover_checkpoints(self.system_prompt) if eval_mode else []
        self.eval_mode = eval_mode

    def _extract_chatmode_system_prompt(self) -> str:
        """Extract the system prompt from the chatmode file.
        Resolution strategy (in order):
          1. Environment variable CHATMODE_PATH (if set)
          2. Sibling/parent directories relative to this script:
             - <evals>/../ (api-review-feedback/)
             - <evals>/../../ (chatmodes/)
          3. First glob match under the top-level chatmodes directory
        Raises FileNotFoundError if not resolved.
        """
        env_override = os.getenv("CHATMODE_PATH")
        if env_override:
            candidate = Path(env_override)
            if candidate.is_file():
                content = candidate.read_text()
                return self._strip_frontmatter(content)
        # Script path: .../api-review-feedback/evals/run_new.py
        evals_dir = Path(__file__).parent
        api_feedback_dir = evals_dir.parent  # .../api-review-feedback
        chatmodes_dir = api_feedback_dir.parent  # .../chatmodes

        # Only look under the top-level chatmodes directory (not the test harness folder itself).
        path = chatmodes_dir / CHATMODE_FILE_NAME

        if path.exists():
            return self._strip_frontmatter(path.read_text())

        if chatmodes_dir.exists():
            matches = list(chatmodes_dir.glob(f"**/{CHATMODE_FILE_NAME}"))
            if matches:
                return self._strip_frontmatter(matches[0].read_text())

        raise FileNotFoundError(
            f"Chatmode file '{CHATMODE_FILE_NAME}' not found. Checked: " +
            ", ".join([str(path)])
        )

    @staticmethod
    def _strip_frontmatter(content: str) -> str:
        """Remove YAML frontmatter if present and return remaining content."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content.strip()

    @staticmethod
    def _create_openai_client():
        """Create and return an OpenAI client based on environment variables."""
        az_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        az_key = os.getenv("AZURE_OPENAI_API_KEY")
        std_key = os.getenv("OPENAI_API_KEY")

        if az_endpoint:
            from openai import AsyncAzureOpenAI
            if az_key:
                return AsyncAzureOpenAI(azure_endpoint=az_endpoint, api_version=API_VERSION, api_key=az_key)
            else:
                credential = DefaultAzureCredential()
                return AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=API_VERSION,
                    azure_ad_token_provider=get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default"),
                )
        else:
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=std_key or az_key)

    @staticmethod
    def _discover_checkpoints(system_prompt: str) -> List[str]:
        """Phase 1: Dynamically extract ordered checkpoint names (#### CHECKPOINT_n:) from the chatmode file.
        Returns a list like ['CHECKPOINT_1', 'CHECKPOINT_2', ...]."""
        pattern = re.compile(r'^####\s+(CHECKPOINT_\d+):', re.MULTILINE)
        found = pattern.findall(system_prompt)
        # Ensure numeric sort in case of out-of-order authoring
        def key(cp: str) -> int:
            try:
                return int(cp.split('_')[1])
            except Exception:
                return 0
        return sorted(dict.fromkeys(found), key=key)

    async def run_aggregated_checkpoint_sequence(self, test_cases: List[Dict[str, Any]], scenario_spec_path: Path, raw_dir: Path, checkpoint_dir: Path) -> Tuple[str, str, List[Tuple[str, Any]]]:
        """Run checkpoints with ALL feedback aggregated into ONE conversation.

        Mimics real user behavior: pasting multiple feedback items at once.
        Runs regular checkpoints for the aggregated changes.

        Returns: (final_response_text, base_user_message, checkpoint_records)
        """
        # Save system prompt at the beginning (directly under raw/)
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "system_prompt.md").write_text(f"```text\n{self.system_prompt}\n```\n")

        # Combine all feedback items into numbered list (like a real user would)
        feedback_items = []
        for i, tc in enumerate(test_cases, 1):
            feedback = tc.get("feedback", "") or tc.get("query", "")
            if feedback:
                feedback_items.append(f"{i}. {feedback}")

        combined_feedback = "\n".join(feedback_items)

        # Build context listing TypeSpec spec files
        context_chunks = []
        for tsp_file in scenario_spec_path.rglob("*.tsp"):
            rel = tsp_file.relative_to(scenario_spec_path)
            context_chunks.append(f"File: {rel}\n```tsp\n{tsp_file.read_text()}\n```")
        context_block = "\n\n".join(context_chunks)

        eval_prefix = "[EVAL_MODE] " if self.eval_mode else ""
        base_user_message = (
            f"{eval_prefix}Here is the API review feedback to implement:\n\n"
            f"{combined_feedback}\n\n"
            f"Context - TypeSpec files in the specification:\n{context_block}\n\n"
            "Please apply all of the above changes to client.tsp. "
            "You will be asked for checkpoints sequentially. Respond exactly as instructed for each step."
        )

        # Save user prompt at the beginning (directly under raw/)
        (raw_dir / "user_prompt.md").write_text(f"```text\n{base_user_message}\n```\n")

        # Model client setup reused across turns
        client = self._create_openai_client()

        # Track conversation history (user/assistant only, system prompt added per-call like VS Code)
        conversation_history = [{"role": "user", "content": base_user_message}]
        checkpoint_records = []

        async def _call(max_tokens: int = 2000) -> str:
            # Mimic VS Code behavior: system prompt in EVERY API call
            messages = [{"role": "system", "content": self.system_prompt}] + conversation_history
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            return content.strip() if content else ""

        def _parse_json_maybe(text: str) -> Any:
            text_stripped = text.strip()
            fenced = re.match(r"```(?:json)?\s*(.*)```", text_stripped, re.DOTALL | re.IGNORECASE)
            if fenced:
                text_stripped = fenced.group(1).strip()
            return json.loads(text_stripped)

        # Run checkpoints
        for cp in self.checkpoints:
            request_msg = (
                f"Produce ONLY the JSON object for {cp}. Do not include text before or after. "
                f"Return a single JSON object (no arrays, no multiple objects)."
            )
            conversation_history.append({"role": "user", "content": request_msg})
            raw = await _call()
            parsed = None
            try:
                parsed = _parse_json_maybe(raw)
            except (json.JSONDecodeError, KeyError, ValueError):
                repair_prompt = (
                    f"Previous output invalid JSON for {cp}. Respond again with ONLY valid JSON for {cp}, no commentary."
                )
                conversation_history.append({"role": "assistant", "content": raw})
                conversation_history.append({"role": "user", "content": repair_prompt})
                raw = await _call()
                try:
                    parsed = _parse_json_maybe(raw)
                except (json.JSONDecodeError, KeyError, ValueError):
                    parsed = {"_error": "unparseable", "raw": raw}
            conversation_history.append({"role": "assistant", "content": raw})
            checkpoint_records.append((cp, parsed))
            # Save checkpoint JSON (create checkpoints dir if needed)
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            (checkpoint_dir / f"{cp}.json").write_text(json.dumps(parsed, indent=2, ensure_ascii=False))

        # Ask for final client.tsp
        final_request = "Now emit the complete client.tsp content in a single ```tsp fenced code block with no extra commentary."
        conversation_history.append({"role": "user", "content": final_request})
        final_response = await _call(max_tokens=4000)
        conversation_history.append({"role": "assistant", "content": final_response})

        # Persist conversation log (directly under raw/)
        convo_path = raw_dir / "conversation.log.jsonl"
        with convo_path.open("w", encoding="utf-8") as fh:
            for m in conversation_history:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")

        return final_response, base_user_message, checkpoint_records

    async def run_checkpoint_sequence(self, test_case: Dict[str, Any], scenario_spec_path: Path, checkpoint_dir: Path) -> Tuple[str, str, List[Tuple[str, Any]]]:
        """Phase 1 multi-turn orchestration.
        - Sends base context once.
        - Iterates each discovered checkpoint requesting ONLY its JSON.
        - Single retry on JSON parse failure.
        - Persists each checkpoint JSON to files.
        - After final checkpoint, requests full client.tsp if not already emitted.

        NOTE: In actual VS Code Copilot Chat, the system prompt is automatically included in every API call.
        In this evaluation harness, we simulate that by re-injecting critical requirements before final generation.

        Returns: (final_response_text, base_user_message, checkpoint_records)
        """
        feedback = test_case.get("feedback", "") or test_case.get("query", "")

        # Build context listing TypeSpec spec files
        context_chunks = []
        for tsp_file in scenario_spec_path.rglob("*.tsp"):
            rel = tsp_file.relative_to(scenario_spec_path)
            context_chunks.append(f"File: {rel}\n```tsp\n{tsp_file.read_text()}\n```")
        context_block = "\n\n".join(context_chunks)

        base_user_message = (
            f"[EVAL_MODE] {feedback}\n\n"
            f"Context - TypeSpec files in the specification:\n{context_block}\n\n"
            "You will be asked for checkpoints sequentially. Respond exactly as instructed for each step."
        )

        # Model client setup reused across turns
        client = self._create_openai_client()

        # Track conversation history (user/assistant only, system prompt added per-call like VS Code)
        conversation_history: List[Dict[str, str]] = [
            {"role": "user", "content": base_user_message},
        ]

        checkpoint_records: List[Tuple[str, Any]] = []

        async def _call(max_tokens: int = 800) -> str:
            # VS Code behavior: system prompt is included in EVERY call
            messages = [{"role": "system", "content": self.system_prompt}] + conversation_history
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            return content.strip() if content else ""

        def _parse_json_maybe(text: str) -> Any:
            text_stripped = text.strip()
            # If model wraps JSON in code fences, strip them
            fenced = re.match(r"```(?:json)?\s*(.*)```", text_stripped, re.DOTALL | re.IGNORECASE)
            if fenced:
                text_stripped = fenced.group(1).strip()
            return json.loads(text_stripped)

        for cp in self.checkpoints:
            request_msg = (
                f"Produce ONLY the JSON object for {cp}. Do not include text before or after. "
                f"Return a single JSON object (no arrays, no multiple objects)."
            )
            conversation_history.append({"role": "user", "content": request_msg})
            raw = await _call()
            # First attempt parse
            parsed = None
            try:
                parsed = _parse_json_maybe(raw)
            except (json.JSONDecodeError, KeyError, ValueError):
                repair_prompt = (
                    f"Previous output invalid JSON for {cp}. Respond again with ONLY valid JSON for {cp}, no commentary."
                )
                conversation_history.append({"role": "assistant", "content": raw})  # record attempt
                conversation_history.append({"role": "user", "content": repair_prompt})
                raw = await _call()
                try:
                    parsed = _parse_json_maybe(raw)
                except (json.JSONDecodeError, KeyError, ValueError):
                    parsed = {"_error": "unparseable", "raw": raw}
            # Record final assistant message
            conversation_history.append({"role": "assistant", "content": raw})
            checkpoint_records.append((cp, parsed))
            # Persist to disk
            (checkpoint_dir / f"{cp}.json").write_text(json.dumps(parsed, indent=2, ensure_ascii=False))

        # Ask for final client.tsp
        final_request = "Now emit the complete client.tsp content in a single ```tsp fenced code block with no extra commentary."
        conversation_history.append({"role": "user", "content": final_request})
        final_response = await _call(max_tokens=4000)  # Higher limit for full file
        conversation_history.append({"role": "assistant", "content": final_response})
        # Persist conversation log (simple jsonl)
        convo_path = checkpoint_dir / "conversation.log.jsonl"
        with convo_path.open("w", encoding="utf-8") as fh:
            for m in conversation_history:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
        return final_response, base_user_message, checkpoint_records


class TypeSpecCompiler:
    """Handles TypeSpec compilation for validation."""

    @staticmethod
    def compile_client_tsp_in_context(client_tsp_content: str, spec_path: Path, build_dir: Path) -> Tuple[bool, str]:
        """
        Compile client.tsp in the context of the specification directory.
        Creates a temp copy of the spec directory under build/, injects client.tsp at the service root, and compiles with --no-emit.

        Args:
            client_tsp_content: Content of the client.tsp file to compile
            spec_path: Path to the specification directory (for import context)
            build_dir: Path to the build directory where temp spec will be created

        Returns:
            Tuple of (success, output)
        """
        try:
            # Find the repo root's node_modules
            current_file = Path(__file__).resolve()
            repo_root = current_file
            while repo_root.parent != repo_root:
                if (repo_root / "package.json").exists() and (repo_root / ".git").exists():
                    break
                repo_root = repo_root.parent

            repo_node_modules = repo_root / "node_modules"

            # Create temp directory under build/
            tmp_spec = build_dir / "temp_spec"

            # Clean up if it already exists
            if tmp_spec.exists():
                shutil.rmtree(tmp_spec)

            # Copy spec files
            shutil.copytree(spec_path, tmp_spec)

            # Find tspconfig.yaml to determine the service root directory
            tspconfig_candidates = list(tmp_spec.rglob("tspconfig.yaml"))
            if tspconfig_candidates:
                # Use the directory containing tspconfig.yaml as the service root
                service_root = tspconfig_candidates[0].parent
            else:
                # Fallback to tmp_spec root if no tspconfig.yaml found
                service_root = tmp_spec

            # Inject the client.tsp into the service root directory
            injected_client_path = service_root / "client.tsp"
            injected_client_path.write_text(client_tsp_content)

            # Run tsp compile on the client.tsp file with --no-emit from the service root
            result = subprocess.run(
                ["tsp", "compile", "./client.tsp", "--no-emit"],
                cwd=service_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
                env={**os.environ, "NODE_PATH": str(repo_node_modules)}
            )

            success = result.returncode == 0
            output = f"COMPILE STDOUT:\n{result.stdout}\n\nCOMPILE STDERR:\n{result.stderr}"

            return success, output

        except subprocess.TimeoutExpired:
            return False, "TypeSpec compilation timed out"
        except (OSError, subprocess.SubprocessError) as e:
            return False, f"Error running TypeSpec compilation: {str(e)}"

class NewChatmodeEvalRunner:
    """Main evaluation runner for the new test structure."""

    def __init__(self, tests_dir: Path, eval_mode: bool = False):
        self.tests_dir = tests_dir
        self.chatmode_runner = TypeSpecChatmodeRunner(eval_mode=eval_mode)
        self.results = []

    def discover_test_scenarios(self) -> List[Path]:
        """Discover all test-* scenario folders."""
        test_scenarios = []
        for item in self.tests_dir.iterdir():
            if item.is_dir() and item.name.startswith("test-"):
                test_scenarios.append(item)
        return sorted(test_scenarios)

    async def run_test_scenario(self, scenario_path: Path) -> List[TypeSpecTestResult]:
        """Run all test cases in a specific test scenario.

        All feedback items are combined into ONE conversation.
        Generates ONE client.tsp with all changes applied.
        Results are saved to: results/{raw,extracted,build}
        """
        print(f"\n🧪 Running test scenario: {scenario_path.name}")

        test_cases_file = scenario_path / "test_cases.json"
        if not test_cases_file.exists():
            return [TypeSpecTestResult(scenario_path.name, False, "test_cases.json not found")]

        try:
            test_cases = json.loads(test_cases_file.read_text())
        except (json.JSONDecodeError, OSError) as e:
            return [TypeSpecTestResult(scenario_path.name, False, f"Invalid test_cases.json: {e}")]

        results_root = scenario_path / "results"

        # Clean up existing results folder before starting new test run
        if results_root.exists():
            shutil.rmtree(results_root)
            print(f"  🧹 Cleaned up existing results folder")

        results_root.mkdir(exist_ok=True)

        spec_path = scenario_path / "specification"
        if not spec_path.exists():
            return [TypeSpecTestResult(scenario_path.name, False, "specification folder not found")]

        # Aggregated mode: process ALL test cases in ONE conversation
        print(f"  📝 Aggregating {len(test_cases)} feedback items into one conversation...")

        raw_dir = results_root / "raw"
        extracted_dir = results_root / "extracted"
        build_dir = results_root / "build"
        checkpoint_dir = raw_dir / "checkpoints"

        try:
            # Run aggregated checkpoint sequence
            final_response, base_user_message, checkpoint_records = await self.chatmode_runner.run_aggregated_checkpoint_sequence(
                test_cases, spec_path, raw_dir, checkpoint_dir
            )

            # Build full raw response including all checkpoint outputs and final response
            full_response_parts = []
            for cp_name, cp_data in checkpoint_records:
                full_response_parts.append(f"=== {cp_name} OUTPUT ===\n")
                full_response_parts.append(json.dumps(cp_data, indent=2, ensure_ascii=False))
                full_response_parts.append("\n\n")

            full_response_parts.append("=== FINAL CLIENT.TSP RESPONSE ===\n")
            full_response_parts.append(final_response)

            (raw_dir / "response.txt").write_text("".join(full_response_parts))

            # Extract only the client.tsp code block from final response
            client_tsp_content = self._extract_client_tsp_from_response(final_response)
            extracted_dir.mkdir(parents=True, exist_ok=True)
            extracted_client_file = extracted_dir / "client.tsp"
            extracted_client_file.write_text(client_tsp_content)

            # Compile the extracted client.tsp in the context of the specification directory
            # This creates a temp copy under build/ with the client.tsp injected to resolve all imports
            compilation_success, compilation_output = TypeSpecCompiler.compile_client_tsp_in_context(
                client_tsp_content, spec_path, build_dir
            )
            build_dir.mkdir(parents=True, exist_ok=True)
            (build_dir / "compile.txt").write_text(compilation_output)
            compilation_success = True
            compilation_output = ""

            # Semantic validation for aggregated mode:
            # Merge validation requirements from ALL test cases
            expected_file = scenario_path / "expected" / "client.tsp"
            merged_validation = {
                "expected_renames": {},
                "required_decorators": [],
                "required_imports": [],
                "required_using": [],
                "forbidden_patterns": []
            }

            # Collect validation from all test cases
            for test_case in test_cases:
                validation_spec = test_case.get("validation", {})

                # Merge expected_renames
                if "expected_renames" in validation_spec:
                    merged_validation["expected_renames"].update(validation_spec["expected_renames"])

                # Merge other validation criteria
                for key in ["required_decorators", "required_imports", "required_using", "forbidden_patterns"]:
                    if key in validation_spec:
                        merged_validation[key].extend(validation_spec[key])

            # Extract validation from expected file if exists
            if expected_file.exists() and not merged_validation["expected_renames"]:
                extracted_validation = self._extract_validation_from_expected(expected_file)
                print(f"    📋 Extracted validation rules from expected/client.tsp")
                merged_validation["required_decorators"] = extracted_validation.get("required_decorators", [])
                merged_validation["required_imports"] = extracted_validation.get("required_imports", [])
                merged_validation["required_using"] = extracted_validation.get("required_using", [])

            # Must have at least one validation source
            has_validation = (
                merged_validation["expected_renames"] or
                merged_validation["required_decorators"] or
                expected_file.exists()
            )
            if not has_validation:
                result = TypeSpecTestResult(
                    scenario_path.name,
                    False,
                    "Aggregated test must have validation rules from test cases or expected/client.tsp"
                )
                return [result]

            semantic_issues = self._validate_semantic(
                client_tsp_content,
                merged_validation,
                compilation_success
            )

            success = len(semantic_issues) == 0
            messages = semantic_issues if semantic_issues else ["All feedback applied successfully"]

            result = TypeSpecTestResult(
                scenario_path.name,
                success,
                "; ".join(messages),
                str(extracted_client_file),
                None,
                diff=None,
                compilation_result=compilation_output
            )

            status_icon = "✅" if success else "❌"
            print(f"    {status_icon} Aggregated result: {result.message}")
            return [result]

        except Exception as e:
            err_result = TypeSpecTestResult(scenario_path.name, False, f"Aggregated test execution error: {e}")
            print(f"    ❌ Aggregated test: ERROR - {e}")
            return [err_result]

    def _extract_validation_from_expected(self, expected_file: Path) -> Dict[str, Any]:
        """Extract validation requirements from expected/client.tsp file.

        Parses the expected file to automatically generate:
        - required_decorators (extracts @@decorator patterns)
        - required_imports (extracts import statements)
        - required_using (extracts using statements)

        Lines marked with // OPTIONAL comment are not validated.
        Lines marked with // REQUIRED comment are validated (default behavior).

        Returns validation spec compatible with _validate_semantic.
        """
        if not expected_file.exists():
            return {}

        content = expected_file.read_text()
        content = expected_file.read_text()
        validation: Dict[str, Any] = {
            "required_decorators": [],
            "required_imports": [],
            "required_using": []
        }
        # Process line by line to respect OPTIONAL markers
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()

            # Skip lines marked as OPTIONAL
            if '// OPTIONAL' in line or '//OPTIONAL' in line:
                continue

            # Extract imports (if not optional)
            import_match = re.match(r'import\s+"([^"]+)"', stripped)
            if import_match:
                validation["required_imports"].append(import_match.group(1))
                continue

            # Extract using statements (if not optional)
            using_match = re.match(r'using\s+([\w.]+)', stripped)
            if using_match:
                validation["required_using"].append(using_match.group(1))
                continue

            # Extract decorators (if not optional)
            # Match: @@decorator(Target.path, "newName", "optional", "params")
            decorator_match = re.match(
                r'@@(\w+)\s*\(\s*([\w.]+)\s*,\s*"([^"]+)"(?:\s*,\s*"([^"]+)")*\s*\)',
                stripped
            )
            if decorator_match:
                decorator_name = decorator_match.group(1)
                target = decorator_match.group(2)
                new_name = decorator_match.group(3)
                language = decorator_match.group(4)  # May be None

                dec_spec = {
                    "decorator": f"@@{decorator_name}",
                    "target": target,
                    "new_name": new_name
                }

                if language:
                    dec_spec["language"] = language

                validation["required_decorators"].append(dec_spec)

        return validation

    def _validate_semantic(self, content: str, validation_spec: Dict[str, Any],
                          compilation_success: bool) -> List[str]:
        """Semantic validation using expected file extraction.

        Validates:
        1. Compilation success (always required)
        2. Required decorators (extracted from expected file)
        3. Required imports
        4. Required using statements
        5. Forbidden patterns

        Returns list of validation issues (empty if all pass).
        """
        issues = []

        # 1. Compilation check (always required)
        if not compilation_success:
            issues.append("Compilation failed")

        # 2. Required decorators (extracted from expected file)
        for dec_spec in validation_spec.get("required_decorators", []):
            success, error_msg = TypeSpecFileComparator.validate_decorator_semantic(content, dec_spec)
            if not success:
                issues.append(error_msg)

        # 3. Required imports
        for imp in validation_spec.get("required_imports", []):
            if f'import "{imp}"' not in content:
                issues.append(f"Missing required import: {imp}")

        # 4. Required using statements
        for using in validation_spec.get("required_using", []):
            if f'using {using}' not in content:
                issues.append(f"Missing required using: {using}")

        # 5. Forbidden patterns
        for forbidden in validation_spec.get("forbidden_patterns", []):
            if forbidden in content:
                issues.append(f"Forbidden pattern found: {forbidden}")

        return issues

    def _extract_client_tsp_from_response(self, response: str) -> str:
        """Extract client.tsp content from chatmode response (robust multi-block handling)."""
        # Try to find complete fenced code blocks
        fence_re = re.compile(r"```(?:tsp|typespec)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)
        blocks = [b.strip() for b in fence_re.findall(response) if b.strip()]
        selected = None
        for b in blocks:
            if 'namespace ' in b and '@client' in b:
                selected = b
                break
        if not selected and blocks:
            selected = max(blocks, key=len)

        # If no complete code block found, look for incomplete code block (missing closing fence)
        if not selected:
            incomplete_re = re.compile(r"```(?:tsp|typespec)?\s*\n(.*)", re.IGNORECASE | re.DOTALL)
            match = incomplete_re.search(response)
            if match:
                selected = match.group(1).strip()

        # Final fallback: collect lines that look like TypeSpec code
        if not selected:
            collected = []
            for raw in response.splitlines():
                s = raw.strip()
                if s.startswith(('import ','using ','namespace ','@client','@@')):
                    collected.append(raw)
            selected = '\n'.join(collected) if collected else response.strip()
        return selected.strip()

    async def run_all_tests(self, scenario_filter: Optional[str] = None) -> List[TypeSpecTestResult]:
        """Run all test scenarios."""
        scenarios = self.discover_test_scenarios()

        if scenario_filter:
            scenarios = [s for s in scenarios if scenario_filter in s.name]

        all_results = []

        for scenario in scenarios:
            scenario_results = await self.run_test_scenario(scenario)
            all_results.extend(scenario_results)

        return all_results

    def generate_report(self, results: List[TypeSpecTestResult]) -> str:
        """Generate a comprehensive test report."""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests

        report = f"""
# TypeSpec Chatmode Evaluation Report

## Summary
- **Total Tests**: {total_tests}
- **Passed**: {passed_tests} ✅
- **Failed**: {failed_tests} ❌
- **Success Rate**: {(passed_tests/total_tests*100):.1f}%

## Test Results
"""

        for result in results:
            status = "✅ PASSED" if result.success else "❌ FAILED"
            report += f"\n### {result.testcase} - {status}\n"
            report += f"**Message**: {result.message}\n"

            if result.diff:
                report += f"\n**Diff**:\n```diff\n{result.diff}\n```\n"

            if result.compilation_result:
                report += f"\n**Compilation Result**:\n```\n{result.compilation_result}\n```\n"

        return report

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TypeSpec Chatmode Evaluation Runner")
    parser.add_argument("--scenario", help="Filter to specific test scenario")
    parser.add_argument("--report", help="Output report file", default="test_report.md")
    parser.add_argument("--eval-mode", action="store_true",
                        help="Enable evaluation mode with checkpoint validation (adds [EVAL_MODE] prefix)")

    args = parser.parse_args()

    # Setup paths
    tests_dir = Path(__file__).parent / "tests"
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        sys.exit(1)

    # Run tests
    runner = NewChatmodeEvalRunner(tests_dir, eval_mode=args.eval_mode)
    if args.eval_mode:
        print("📊 Evaluation mode: Running with checkpoint validation")
    else:
        print("⚡ Fast mode: Skipping checkpoint validation")
    results = await runner.run_all_tests(args.scenario)

    # Generate and save report
    report = runner.generate_report(results)
    requested_report_path = Path(args.report)
    if requested_report_path.is_absolute():
        report_file = requested_report_path
    else:
        # Ensure report is written under the tests/ folder for clearer artifact collation
        report_file = tests_dir / requested_report_path.name
    report_file.write_text(report)
    print(f"\n📊 Test report saved to: {report_file}")

    # Print summary
    total = len(results)
    passed = sum(1 for r in results if r.success)
    print(f"\n🎯 Final Results: {passed}/{total} tests passed ({(passed/total*100):.1f}%)")

    # Exit with non-zero code if any tests failed
    sys.exit(0 if passed == total else 1)

if __name__ == "__main__":
    asyncio.run(main())