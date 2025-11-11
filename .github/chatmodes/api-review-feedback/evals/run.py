#!/usr/bin/env python3
"""
Enhanced evaluation runner for the API Review Feedback chatmode agent.
Supports new test structure with isolated scenarios and file-based validation.
"""

import os
import asyncio
import json
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import dotenv
except ImportError:
    print("Error: Required packages not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

# Import modular components
from _test_result import TypeSpecTestResult
from _file_comparator import TypeSpecFileComparator
from _compiler import TypeSpecCompiler
from _chatmode_runner import TypeSpecChatmodeRunner

# Load environment variables (root .env plus chatmode-local .env if present)
dotenv.load_dotenv()  # default search upwards from CWD
chatmode_env = Path(__file__).parent.parent / ".env"
if chatmode_env.exists():
    dotenv.load_dotenv(dotenv_path=chatmode_env, override=True)

CHATMODE_FILE_NAME = "api-review-feedback-smart.chatmode.md"


class NewChatmodeEvalRunner:
    """Main evaluation runner for the new test structure."""

    def __init__(self, tests_dir: Path, eval_mode: bool = False, provider: str = "openai", model: Optional[str] = None):
        self.tests_dir = tests_dir
        self.chatmode_runner = TypeSpecChatmodeRunner(eval_mode=eval_mode, provider=provider, model=model)
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

            # Print paths for extracted file
            print(f"    📄 Extracted client.tsp: {extracted_client_file.absolute()}")

            # Compile the extracted client.tsp in the context of the specification directory
            # This creates a temp copy under build/ with the client.tsp injected to resolve all imports
            compilation_success, compilation_output = TypeSpecCompiler.compile_client_tsp_in_context(
                client_tsp_content, spec_path, build_dir
            )
            build_dir.mkdir(parents=True, exist_ok=True)
            (build_dir / "compile.txt").write_text(compilation_output)

            # Semantic validation for aggregated mode:
            # Merge validation requirements from ALL test cases
            expected_file = scenario_path / "expected" / "client.tsp"

            # Print path for expected file (always, as per README rules)
            print(f"    📋 Expected client.tsp: {expected_file.absolute()}")

            merged_validation = {
                "expected_renames": {},
                "expected_visibility": {},
                "expected_types": {},
                "expected_clients": {},
                "expected_usage": {},
                "expected_decorators": []
            }

            # Merge all validation requirements from test cases
            for tc in test_cases:
                val = tc.get("validation", {})
                if "expected_renames" in val:
                    merged_validation["expected_renames"].update(val["expected_renames"])
                if "expected_visibility" in val:
                    merged_validation["expected_visibility"].update(val["expected_visibility"])
                if "expected_types" in val:
                    merged_validation["expected_types"].update(val["expected_types"])
                if "expected_clients" in val:
                    merged_validation["expected_clients"].update(val["expected_clients"])
                if "expected_usage" in val:
                    merged_validation["expected_usage"].update(val["expected_usage"])
                if "expected_decorators" in val:
                    merged_validation["expected_decorators"].extend(val["expected_decorators"])

            # Validate the extracted client.tsp content
            validation_success, validation_msg = TypeSpecFileComparator.validate_file_content(
                client_tsp_content,
                merged_validation
            )

            # Compare with expected file if it exists
            expected_content = None
            diff_output = None
            if expected_file.exists():
                expected_content = expected_file.read_text()
                diff_output = TypeSpecFileComparator.compute_diff(expected_content, client_tsp_content)

            if not validation_success:
                result = TypeSpecTestResult(
                    scenario_path.name,
                    False,
                    f"❌ Validation failed: {validation_msg}",
                    generated_file=str(extracted_client_file.absolute()),
                    expected_file=str(expected_file.absolute()) if expected_file.exists() else None,
                    diff=diff_output,
                    compilation_result=compilation_output
                )
            elif not compilation_success:
                result = TypeSpecTestResult(
                    scenario_path.name,
                    False,
                    f"❌ Compilation failed",
                    generated_file=str(extracted_client_file.absolute()),
                    expected_file=str(expected_file.absolute()) if expected_file.exists() else None,
                    diff=diff_output,
                    compilation_result=compilation_output
                )
            else:
                result = TypeSpecTestResult(
                    scenario_path.name,
                    True,
                    "✅ All checks passed",
                    generated_file=str(extracted_client_file.absolute()),
                    expected_file=str(expected_file.absolute()) if expected_file.exists() else None,
                    diff=diff_output,
                    compilation_result=compilation_output
                )

            print(f"  {result.message}")
            return [result]

        except Exception as e:
            import traceback
            error_msg = f"❌ Exception during test: {e}\n{traceback.format_exc()}"
            print(f"  {error_msg}")
            return [TypeSpecTestResult(scenario_path.name, False, error_msg)]

    @staticmethod
    def _extract_client_tsp_from_response(response: str) -> str:
        """Extract client.tsp content from model response."""
        import re
        # Match ```tsp or ```typespec code blocks
        match = re.search(r'```(?:tsp|typespec)\s*\n(.*?)\n```', response, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        # Fallback: return entire response if no code block found
        return response.strip()

    async def run_all_scenarios(self, specific_scenario: Optional[str] = None):
        """Run all discovered test scenarios (or a specific one if provided)."""
        scenarios = self.discover_test_scenarios()

        if specific_scenario:
            scenarios = [s for s in scenarios if s.name == specific_scenario]
            if not scenarios:
                print(f"❌ Test scenario '{specific_scenario}' not found")
                return

        if not scenarios:
            print("❌ No test scenarios found in tests/ directory")
            return

        print(f"📊 Found {len(scenarios)} test scenario(s)")

        all_results = []
        for scenario in scenarios:
            results = await self.run_test_scenario(scenario)
            all_results.extend(results)
            self.results.extend(results)

        self._generate_summary_report(all_results)

    def _generate_summary_report(self, results: List[TypeSpecTestResult]):
        """Generate a summary report of all test results."""
        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed

        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total scenarios: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        print("=" * 80)

        if failed > 0:
            print("\n❌ Failed scenarios:")
            for r in results:
                if not r.success:
                    print(f"  - {r.testcase}: {r.message}")

        # Write detailed markdown report
        report_path = self.tests_dir / "test_report.md"
        with report_path.open("w") as f:
            f.write("# Chatmode Evaluation Report\n\n")
            f.write(f"**Total Scenarios:** {total}  \n")
            f.write(f"**Passed:** {passed}  \n")
            f.write(f"**Failed:** {failed}  \n")
            f.write(f"**Success Rate:** {(passed/total*100):.1f}%\n\n" if total > 0 else "**Success Rate:** N/A\n\n")

            f.write("## Test Results\n\n")
            for r in results:
                status = "✅ PASS" if r.success else "❌ FAIL"
                f.write(f"### {status} - {r.testcase}\n\n")
                f.write(f"**Message:** {r.message}\n\n")

                if r.generated_file:
                    f.write(f"**Generated File:** `{r.generated_file}`\n\n")
                if r.expected_file:
                    f.write(f"**Expected File:** `{r.expected_file}`\n\n")

                if r.compilation_result:
                    f.write(f"**Compilation Output:**\n```\n{r.compilation_result}\n```\n\n")

                if r.diff:
                    f.write(f"**Diff (Expected vs Generated):**\n```diff\n{r.diff}\n```\n\n")

        print(f"\n📝 Detailed report saved to: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run chatmode evaluations")
    parser.add_argument(
        "--scenario",
        type=str,
        help="Run a specific test scenario (e.g., 'test-rename-operation')"
    )
    parser.add_argument(
        "--eval-mode",
        action="store_true",
        help="Enable EVAL_MODE for checkpoint validation"
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use (openai or anthropic). Default: openai"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model to use (e.g., gpt-4o, gpt-4o-mini, claude-3-5-sonnet-20241022)"
    )
    args = parser.parse_args()

    tests_dir = Path(__file__).parent / "tests"
    if not tests_dir.exists():
        print(f"❌ Tests directory not found: {tests_dir}")
        sys.exit(1)

    runner = NewChatmodeEvalRunner(
        tests_dir,
        eval_mode=args.eval_mode,
        provider=args.provider,
        model=args.model
    )
    asyncio.run(runner.run_all_scenarios(specific_scenario=args.scenario))


if __name__ == "__main__":
    main()
