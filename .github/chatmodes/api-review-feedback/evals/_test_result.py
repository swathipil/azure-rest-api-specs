#!/usr/bin/env python3
"""Data classes for test results."""

from typing import Optional


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
