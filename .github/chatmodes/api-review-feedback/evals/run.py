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
import time
import sys
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import difflib
import re

try:
    import jsonlines
    import dotenv
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    from deepdiff import DeepDiff
    import pytest
except ImportError:
    print("Error: Required packages not installed. Run: pip install -r requirements.txt")
    print("Required: jsonlines python-dotenv azure-identity deepdiff pytest")
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
    """Handles comparison of TypeSpec files with semantic understanding."""
    
    @staticmethod
    def normalize_typespec_content(content: str) -> Dict[str, List[str]]:
        """
        Parse and normalize TypeSpec content for comparison.
        Returns structured representation of imports, using statements, namespace, and decorators.
        """
        raw_lines = content.split('\n')
        structure = {
            'imports': [],
            'using_statements': [],
            'namespace': None,
            'decorators': [],
            'other': []
        }

        i = 0
        while i < len(raw_lines):
            line = raw_lines[i].strip()
            if not line or line.startswith('//'):
                i += 1
                continue

            if line.startswith('@client') or line.startswith('@@'):
                block_lines = [line]
                open_parens = line.count('(') - line.count(')')
                open_braces = line.count('{') - line.count('}')
                j = i + 1
                while (open_parens > 0 or open_braces > 0) and j < len(raw_lines):
                    nxt = raw_lines[j]
                    block_lines.append(nxt.strip())
                    open_parens += nxt.count('(') - nxt.count(')')
                    open_braces += nxt.count('{') - nxt.count('}')
                    j += 1
                i = j
                cleaned = ' '.join(bl.strip() for bl in block_lines if bl.strip())
                cleaned = re.sub(r'\s+', ' ', cleaned).rstrip(';')
                structure['decorators'].append(cleaned)
                continue

            if line.startswith('import '):
                structure['imports'].append(line.rstrip(';'))
            elif line.startswith('using '):
                structure['using_statements'].append(line.rstrip(';'))
            elif line.startswith('namespace '):
                structure['namespace'] = line
            else:
                structure['other'].append(line)
            i += 1

        for key in ('imports','using_statements','decorators'):
            structure[key].sort()
        return structure
    
    @staticmethod
    def compare_typespec_files(expected_path: Path, generated_path: Path) -> Tuple[bool, str, Dict]:
        """
        Compare two TypeSpec files semantically.
        Returns (is_match, diff_message, detailed_comparison)
        """
        try:
            expected_content = expected_path.read_text().strip()
            generated_content = generated_path.read_text().strip()
            
            expected_structure = TypeSpecFileComparator.normalize_typespec_content(expected_content)
            generated_structure = TypeSpecFileComparator.normalize_typespec_content(generated_content)
            
            # Use DeepDiff for detailed comparison
            diff = DeepDiff(expected_structure, generated_structure, ignore_order=True)
            
            if not diff:
                return True, "Files match semantically", {}
            
            # Generate human-readable diff message
            diff_messages = []
            
            if 'values_changed' in diff:
                for key, change in diff['values_changed'].items():
                    diff_messages.append(f"Changed {key}: '{change['old_value']}' -> '{change['new_value']}'")
            
            if 'iterable_item_added' in diff:
                for key, items in diff['iterable_item_added'].items():
                    diff_messages.append(f"Missing in generated: {key} = {items}")
            
            if 'iterable_item_removed' in diff:
                for key, items in diff['iterable_item_removed'].items():
                    diff_messages.append(f"Extra in generated: {key} = {items}")
            
            diff_message = "\n".join(diff_messages)
            
            # Also provide traditional line-by-line diff for context
            line_diff = list(difflib.unified_diff(
                expected_content.splitlines(keepends=True),
                generated_content.splitlines(keepends=True),
                fromfile='expected/client.tsp',
                tofile='results/client.tsp',
                lineterm=''
            ))
            
            return False, diff_message, {
                'semantic_diff': diff,
                'line_diff': ''.join(line_diff)
            }
            
        except Exception as e:
            return False, f"Error comparing files: {str(e)}", {}

class TypeSpecChatmodeRunner:
    """Handles running the chatmode against test scenarios."""
    
    def __init__(self):
        self.system_prompt = self._extract_chatmode_system_prompt()
        self.checkpoints = self._discover_checkpoints(self.system_prompt)
    
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
    
    async def run_checkpoint_sequence(self, test_case: Dict[str, Any], scenario_spec_path: Path, checkpoint_dir: Path) -> Tuple[str, str, List[Tuple[str, Any]]]:
        """Phase 1 multi-turn orchestration.
        - Sends base context once.
        - Iterates each discovered checkpoint requesting ONLY its JSON.
        - Single retry on JSON parse failure.
        - Persists each checkpoint JSON to files.
        - After final checkpoint, requests full client.tsp if not already emitted.
        Returns: (final_response_text, base_user_message, checkpoint_records)
        """
        feedback = test_case.get("feedback", "") or test_case.get("query", "")
        language = test_case.get("language", "")

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
        az_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        az_key = os.getenv("AZURE_OPENAI_API_KEY")
        std_key = os.getenv("OPENAI_API_KEY")
        if az_endpoint:
            from openai import AsyncAzureOpenAI
            if az_key:
                client = AsyncAzureOpenAI(azure_endpoint=az_endpoint, api_version=API_VERSION, api_key=az_key)
            else:
                credential = DefaultAzureCredential()
                client = AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=API_VERSION,
                    azure_ad_token_provider=get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default"),
                )
        else:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=std_key or az_key)

        conversation: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": base_user_message},
        ]

        checkpoint_records: List[Tuple[str, Any]] = []

        async def _call(messages: List[Dict[str, str]]) -> str:
            resp = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=800,
            )
            return resp.choices[0].message.content.strip()

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
            conversation.append({"role": "user", "content": request_msg})
            raw = await _call(conversation)
            # First attempt parse
            parsed = None
            retry_used = False
            try:
                parsed = _parse_json_maybe(raw)
            except Exception:
                retry_used = True
                repair_prompt = (
                    f"Previous output invalid JSON for {cp}. Respond again with ONLY valid JSON for {cp}, no commentary."
                )
                conversation.append({"role": "assistant", "content": raw})  # record attempt
                conversation.append({"role": "user", "content": repair_prompt})
                raw = await _call(conversation)
                try:
                    parsed = _parse_json_maybe(raw)
                except Exception:
                    parsed = {"_error": "unparseable", "raw": raw}
            # Record final assistant message
            conversation.append({"role": "assistant", "content": raw})
            checkpoint_records.append((cp, parsed))
            # Persist to disk
            (checkpoint_dir / f"{cp}.json").write_text(json.dumps(parsed, indent=2, ensure_ascii=False))

        # Ask for final client.tsp
        final_request = (
            "Now emit the complete client.tsp content in a single ```tsp fenced code block with no extra commentary." \
            " Ensure proper imports, using statements, namespace, and decorators."
        )
        conversation.append({"role": "user", "content": final_request})
        final_response = await _call(conversation)
        conversation.append({"role": "assistant", "content": final_response})
        # Persist conversation log (simple jsonl)
        convo_path = checkpoint_dir / "conversation.log.jsonl"
        with convo_path.open("w", encoding="utf-8") as fh:
            for m in conversation:
                fh.write(json.dumps(m, ensure_ascii=False) + "\n")
        return final_response, base_user_message, checkpoint_records
        
        
    
    async def run_chatmode_on_scenario(self, test_case: Dict[str, Any], 
                                     scenario_spec_path: Path) -> Tuple[str, str]:
        """
        Run the chatmode on a specific test scenario.
        """
        feedback = test_case.get("feedback", "")
        language = test_case.get("language", "")
        
        # Build context from the scenario specification folder
        context_files = []
        for tsp_file in scenario_spec_path.rglob("*.tsp"):
            relative_path = tsp_file.relative_to(scenario_spec_path)
            content = tsp_file.read_text()
            context_files.append(f"File: {relative_path}\n```tsp\n{content}\n```")
        
        context = "\n\n".join(context_files)
        
        # Create user message with full context
        user_message = f"""[EVAL_MODE] {feedback}

Context - TypeSpec files in the specification:
{context}

Please provide the complete client.tsp file content needed to implement this feedback.
Ensure proper imports, using statements, namespace declaration, and decorator syntax."""

        # Call OpenAI API
        az_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        az_key = os.getenv("AZURE_OPENAI_API_KEY")
        std_key = os.getenv("OPENAI_API_KEY")

        if az_endpoint:
            from openai import AsyncAzureOpenAI
            if az_key:
                # Use API key authentication
                client = AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=API_VERSION,
                    api_key=az_key,
                )
            else:
                # Fall back to AAD token provider
                credential = DefaultAzureCredential()
                client = AsyncAzureOpenAI(
                    azure_endpoint=az_endpoint,
                    api_version=API_VERSION,
                    azure_ad_token_provider=get_bearer_token_provider(
                        credential, "https://cognitiveservices.azure.com/.default"
                    ),
                )
        else:
            # Allow AZURE_OPENAI_API_KEY to stand in as generic OPENAI key if standard key missing
            effective_key = std_key or az_key
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=effective_key)
        
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.choices[0].message.content.strip(), user_message
            
        except Exception as e:
            return f"Error calling chatmode via OpenAI: {str(e)}", user_message

class TypeSpecCompiler:
    """Handles TypeSpec compilation for validation."""
    
    @staticmethod
    def compile_typespec_project(project_path: Path) -> Tuple[bool, str]:
        """
        Compile a TypeSpec project and return success status and output.
        """
        try:
            # Ensure we have tspconfig.yaml
            tspconfig_path = project_path / "tspconfig.yaml"
            if not tspconfig_path.exists():
                # Create minimal tspconfig.yaml
                tspconfig_content = """options:
  emit:
    - "@typespec/openapi3"
"""
                tspconfig_path.write_text(tspconfig_content)
            
            # Run tsp compile
            result = subprocess.run(
                ["tsp", "compile", "."],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
            return success, output
            
        except subprocess.TimeoutExpired:
            return False, "TypeSpec compilation timed out"
        except Exception as e:
            return False, f"Error running TypeSpec compilation: {str(e)}"

class NewChatmodeEvalRunner:
    """Main evaluation runner for the new test structure."""
    
    def __init__(self, tests_dir: Path):
        self.tests_dir = tests_dir
        self.chatmode_runner = TypeSpecChatmodeRunner()
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
        New logic:
          - Per test-case artifact directories: results/<testcase>/{raw,extracted,build,diff}
          - Preserve raw model response
          - Extract client.tsp content -> extracted/client.tsp
          - Compile in an isolated temp workspace that copies specification + injected client.tsp
          - Compare against expected/client.tsp (single expected for now)
        """
        print(f"\n🧪 Running test scenario: {scenario_path.name}")

        test_cases_file = scenario_path / "test_cases.json"
        if not test_cases_file.exists():
            return [TypeSpecTestResult(scenario_path.name, False, "test_cases.json not found")]

        try:
            test_cases = json.loads(test_cases_file.read_text())
        except Exception as e:
            return [TypeSpecTestResult(scenario_path.name, False, f"Invalid test_cases.json: {e}")]

        results_root = scenario_path / "results"
        results_root.mkdir(exist_ok=True)

        expected_file = scenario_path / "expected" / "client.tsp"
        has_expected = expected_file.exists()

        scenario_results: List[TypeSpecTestResult] = []
        spec_path = scenario_path / "specification"
        if not spec_path.exists():
            return [TypeSpecTestResult(scenario_path.name, False, "specification folder not found")]

        for test_case in test_cases:
            if not test_case:
                continue
            testcase_name = test_case.get("testcase", "unnamed")
            safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", testcase_name)
            print(f"  ⚡ Running test case: {testcase_name}")

            per_test_dir = results_root / safe_name
            raw_dir = per_test_dir / "raw"
            extracted_dir = per_test_dir / "extracted"
            build_dir = per_test_dir / "build"
            diff_dir = per_test_dir / "diff"
            for d in (raw_dir, extracted_dir, build_dir, diff_dir):
                d.mkdir(parents=True, exist_ok=True)

            try:
                checkpoint_dir = raw_dir / "checkpoints"
                checkpoint_dir.mkdir(parents=True, exist_ok=True)
                # Phase 1 multi-turn sequence
                response, base_user_message, checkpoint_records = await self.chatmode_runner.run_checkpoint_sequence(
                    test_case, spec_path, checkpoint_dir
                )
                (raw_dir / "response.txt").write_text(response)
                (raw_dir / "user_prompt.md").write_text(f"```text\n{base_user_message}\n```\n")
                (raw_dir / "system_prompt.md").write_text(f"```text\n{self.chatmode_runner.system_prompt}\n```\n")

                client_tsp_content = self._extract_client_tsp_from_response(response)
                extracted_client_file = extracted_dir / "client.tsp"
                extracted_client_file.write_text(client_tsp_content)

                # Naive expected decorator presence check (placeholder for richer parser)
                expected_decorators = test_case.get("expected_decorators", []) or []
                missing_decorators = [d for d in expected_decorators if d not in client_tsp_content]

                # Temp workspace compile
                with tempfile.TemporaryDirectory(prefix="tsp_eval_") as tmpdir:
                    tmp_spec = Path(tmpdir) / "spec"
                    shutil.copytree(spec_path, tmp_spec)
                    injected_client_path = tmp_spec / "client.tsp"
                    injected_client_path.write_text(client_tsp_content)

                    compilation_success, compilation_output = TypeSpecCompiler.compile_typespec_project(tmp_spec)
                    (build_dir / "compile.txt").write_text(compilation_output)

                diff_text = ""
                is_match = False
                diff_message = "No expected file"
                if has_expected:
                    is_match, diff_message, detailed_diff = TypeSpecFileComparator.compare_typespec_files(expected_file, extracted_client_file)
                    diff_text = detailed_diff.get("line_diff", "") if detailed_diff else ""
                    if diff_text:
                        (diff_dir / "unified.diff").write_text(diff_text)

                success = is_match and compilation_success and not missing_decorators
                messages = []
                if not has_expected:
                    messages.append("Expected client.tsp file not found")
                else:
                    if not is_match:
                        messages.append(f"Output mismatch: {diff_message}")
                if not compilation_success:
                    messages.append("Compilation failed")
                if missing_decorators:
                    messages.append("Missing decorators: " + ", ".join(missing_decorators))
                if not messages:
                    messages.append("Test passed: matches expected, compiles, decorators present")

                result = TypeSpecTestResult(
                    testcase_name,
                    success,
                    "; ".join(messages),
                    str(extracted_client_file),
                    str(expected_file) if has_expected else None,
                    diff=diff_text,
                    compilation_result=compilation_output
                )
                scenario_results.append(result)
                status_icon = "✅" if success else "❌"
                print(f"    {status_icon} {testcase_name}: {result.message}")
            except Exception as e:
                err_result = TypeSpecTestResult(testcase_name, False, f"Test execution error: {e}")
                scenario_results.append(err_result)
                print(f"    ❌ {testcase_name}: ERROR - {e}")

        return scenario_results
    
    def _extract_client_tsp_from_response(self, response: str) -> str:
        """Extract client.tsp content from chatmode response (robust multi-block handling)."""
        fence_re = re.compile(r"```(?:tsp|typespec)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)
        blocks = [b.strip() for b in fence_re.findall(response) if b.strip()]
        selected = None
        for b in blocks:
            if 'namespace ' in b and '@client' in b:
                selected = b
                break
        if not selected and blocks:
            selected = max(blocks, key=len)
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
    
    args = parser.parse_args()
    
    # Setup paths
    tests_dir = Path(__file__).parent / "tests"
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        sys.exit(1)
    
    # Run tests
    runner = NewChatmodeEvalRunner(tests_dir)
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