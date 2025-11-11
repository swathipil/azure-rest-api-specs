#!/usr/bin/env python3
"""TypeSpec file semantic validation and comparison."""

import re
from typing import Dict, List, Optional, Any, Tuple


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

    @staticmethod
    def validate_file_content(content: str, validation_spec: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate TypeSpec file content against validation specification.
        
        Args:
            content: TypeSpec file content
            validation_spec: Validation requirements with keys:
                - expected_decorators: List of decorator specs to validate
                - expected_renames: Dict (deprecated, converts to decorators)
                - expected_visibility: Dict (deprecated, converts to decorators)
                - expected_types: Dict (deprecated, converts to decorators)
                - expected_clients: Dict (deprecated, converts to decorators)
                - expected_usage: Dict (deprecated, converts to decorators)
        
        Returns:
            (success, error_message)
        """
        issues = []
        
        # Process expected_decorators (new format)
        for dec_spec in validation_spec.get("expected_decorators", []):
            success, error_msg = TypeSpecFileComparator.validate_decorator_semantic(content, dec_spec)
            if not success:
                issues.append(error_msg)
        
        # Legacy format support: convert old validation formats to decorator specs
        # expected_renames: {"Azure.AI.OpenAI.ChatCompletions.createChatCompletion": {"python": "create"}}
        for target, renames in validation_spec.get("expected_renames", {}).items():
            for lang, new_name in renames.items():
                dec_spec = {
                    "decorator": "@@clientName",
                    "target": target,
                    "new_name": new_name,
                    "language": lang
                }
                success, error_msg = TypeSpecFileComparator.validate_decorator_semantic(content, dec_spec)
                if not success:
                    issues.append(error_msg)
        
        if issues:
            return False, "; ".join(issues)
        return True, "All validations passed"
    
    @staticmethod
    def compute_diff(expected: str, generated: str) -> str:
        """Compute diff between expected and generated content.
        
        Args:
            expected: Expected file content
            generated: Generated file content
            
        Returns:
            Diff string
        """
        import difflib
        expected_lines = expected.splitlines(keepends=True)
        generated_lines = generated.splitlines(keepends=True)
        diff = difflib.unified_diff(
            expected_lines,
            generated_lines,
            fromfile='expected',
            tofile='generated',
            lineterm=''
        )
        return ''.join(diff)

