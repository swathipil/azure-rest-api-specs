#!/usr/bin/env python3
"""TypeSpec chatmode runner - handles LLM interaction for test scenarios."""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple

from _llm_client import create_llm_client, call_llm, get_model_name


# Chatmode file name
CHATMODE_FILE_NAME = "api-review-feedback-smart.chatmode.md"


class TypeSpecChatmodeRunner:
    """Handles running the chatmode against test scenarios."""

    def __init__(self, eval_mode: bool = False, provider: str = "openai", model: str = None):
        self.system_prompt = self._extract_chatmode_system_prompt()
        self.checkpoints = self._discover_checkpoints(self.system_prompt) if eval_mode else []
        self.eval_mode = eval_mode
        self.provider = provider
        self.model_name = model or get_model_name(provider)

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
        
        # Script path: .../api-review-feedback/evals/chatmode_runner.py
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
            f"Chatmode file '{CHATMODE_FILE_NAME}' not found. Checked: {path}"
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

    async def run_aggregated_checkpoint_sequence(
        self, 
        test_cases: List[Dict[str, Any]], 
        scenario_spec_path: Path, 
        raw_dir: Path, 
        checkpoint_dir: Path
    ) -> Tuple[str, str, List[Tuple[str, Any]]]:
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
        client = create_llm_client(self.provider)

        # Track conversation history (user/assistant only, system prompt added per-call like VS Code)
        conversation_history = [{"role": "user", "content": base_user_message}]
        checkpoint_records = []

        async def _call(max_tokens: int = 2000) -> str:
            # Mimic VS Code behavior: system prompt in EVERY API call
            messages = [{"role": "system", "content": self.system_prompt}] + conversation_history
            return await call_llm(client, messages, self.model_name, max_tokens, self.provider)

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

    async def run_checkpoint_sequence(
        self, 
        test_case: Dict[str, Any], 
        scenario_spec_path: Path, 
        checkpoint_dir: Path
    ) -> Tuple[str, str, List[Tuple[str, Any]]]:
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
        client = create_llm_client(self.provider)

        # Track conversation history (user/assistant only, system prompt added per-call like VS Code)
        conversation_history: List[Dict[str, str]] = [
            {"role": "user", "content": base_user_message},
        ]

        checkpoint_records: List[Tuple[str, Any]] = []

        async def _call(max_tokens: int = 800) -> str:
            # VS Code behavior: system prompt is included in EVERY call
            messages = [{"role": "system", "content": self.system_prompt}] + conversation_history
            return await call_llm(client, messages, self.model_name, max_tokens, self.provider)

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
