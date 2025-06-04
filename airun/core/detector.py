"""
Script type detection module for AIRun.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class ScriptType(Enum):
    """Supported script types."""
    PYTHON = "python"
    SHELL = "shell"
    NODEJS = "nodejs"
    PHP = "php"
    UNKNOWN = "unknown"


class ScriptDetector:
    """Detects script type based on file extension, shebang, and content analysis."""

    EXTENSION_MAP = {
        '.py': ScriptType.PYTHON,
        '.pyw': ScriptType.PYTHON,
        '.py3': ScriptType.PYTHON,
        '.sh': ScriptType.SHELL,
        '.bash': ScriptType.SHELL,
        '.zsh': ScriptType.SHELL,
        '.fish': ScriptType.SHELL,
        '.js': ScriptType.NODEJS,
        '.mjs': ScriptType.NODEJS,
        '.ts': ScriptType.NODEJS,
        '.jsx': ScriptType.NODEJS,
        '.tsx': ScriptType.NODEJS,
        '.php': ScriptType.PHP,
        '.php3': ScriptType.PHP,
        '.php4': ScriptType.PHP,
        '.php5': ScriptType.PHP,
        '.phtml': ScriptType.PHP,
    }

    SHEBANG_PATTERNS = {
        r'#!/usr/bin/python\d*': ScriptType.PYTHON,
        r'#!/usr/bin/env python\d*': ScriptType.PYTHON,
        r'#!/bin/bash': ScriptType.SHELL,
        r'#!/bin/sh': ScriptType.SHELL,
        r'#!/usr/bin/env bash': ScriptType.SHELL,
        r'#!/bin/zsh': ScriptType.SHELL,
        r'#!/usr/bin/env zsh': ScriptType.SHELL,
        r'#!/usr/bin/node': ScriptType.NODEJS,
        r'#!/usr/bin/env node': ScriptType.NODEJS,
        r'#!/usr/bin/php': ScriptType.PHP,
        r'#!/usr/bin/env php': ScriptType.PHP,
    }

    CONTENT_PATTERNS = {
        ScriptType.PYTHON: [
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*\(',
            r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',
            r'print\s*\(',
        ],
        ScriptType.SHELL: [
            r'echo\s+',
            r'export\s+\w+=',
            r'chmod\s+',
            r'mkdir\s+',
            r'cd\s+',
            r'\$\{\w+\}',
            r'for\s+\w+\s+in\s+',
            r'while\s+\[',
        ],
        ScriptType.NODEJS: [
            r'console\.log\s*\(',
            r'require\s*\(',
            r'import\s+.+\s+from\s+',
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'=>\s*\{',
        ],
        ScriptType.PHP: [
            r'<\?php',
            r'echo\s+',
            r'\$_GET\[',
            r'\$_POST\[',
            r'function\s+\w+\s*\(',
            r'\$\w+\s*=',
            r'->',
        ]
    }

    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the script detector.

        Args:
            confidence_threshold: Minimum confidence score for content-based detection
        """
        self.confidence_threshold = confidence_threshold

    def detect_type(self, filepath: str) -> ScriptType:
        """
        Detect script type using multiple methods.

        Args:
            filepath: Path to the script file

        Returns:
            Detected script type
        """
        path = Path(filepath)

        # 1. Check file extension
        extension_type = self._detect_by_extension(path)
        if extension_type != ScriptType.UNKNOWN:
            return extension_type

        # 2. Check shebang
        shebang_type = self._detect_by_shebang(filepath)
        if shebang_type != ScriptType.UNKNOWN:
            return shebang_type

        # 3. Content analysis
        content_type = self._detect_by_content(filepath)
        if content_type != ScriptType.UNKNOWN:
            return content_type

        return ScriptType.UNKNOWN

    def _detect_by_extension(self, path: Path) -> ScriptType:
        """Detect script type by file extension."""
        suffix = path.suffix.lower()
        return self.EXTENSION_MAP.get(suffix, ScriptType.UNKNOWN)

    def _detect_by_shebang(self, filepath: str) -> ScriptType:
        """Detect script type by shebang line."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()

            for pattern, script_type in self.SHEBANG_PATTERNS.items():
                if re.match(pattern, first_line):
                    return script_type

        except (IOError, UnicodeDecodeError):
            pass

        return ScriptType.UNKNOWN

    def _detect_by_content(self, filepath: str) -> ScriptType:
        """Detect script type by analyzing file content."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (IOError, UnicodeDecodeError):
            return ScriptType.UNKNOWN

        scores = {}

        for script_type, patterns in self.CONTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                score += matches

            # Normalize score by content length
            normalized_score = score / max(len(content.split('\n')), 1)
            scores[script_type] = normalized_score

        # Find the type with highest score
        if scores:
            best_type = max(scores, key=scores.get)
            if scores[best_type] >= self.confidence_threshold:
                return best_type

        return ScriptType.UNKNOWN

    def get_confidence_scores(self, filepath: str) -> Dict[ScriptType, float]:
        """
        Get confidence scores for all script types.

        Args:
            filepath: Path to the script file

        Returns:
            Dictionary mapping script types to confidence scores
        """
        scores = {script_type: 0.0 for script_type in ScriptType}

        path = Path(filepath)

        # Extension-based score
        extension_type = self._detect_by_extension(path)
        if extension_type != ScriptType.UNKNOWN:
            scores[extension_type] += 1.0

        # Shebang-based score
        shebang_type = self._detect_by_shebang(filepath)
        if shebang_type != ScriptType.UNKNOWN:
            scores[shebang_type] += 0.8

        # Content-based scores
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for script_type, patterns in self.CONTENT_PATTERNS.items():
                pattern_score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                    pattern_score += matches

                # Normalize by content length
                normalized_score = pattern_score / max(len(content.split('\n')), 1)
                scores[script_type] += min(normalized_score, 0.5)  # Cap content score

        except (IOError, UnicodeDecodeError):
            pass

        return scores

    def is_executable(self, filepath: str) -> bool:
        """Check if file has executable permissions."""
        try:
            path = Path(filepath)
            return path.is_file() and path.stat().st_mode & 0o111
        except (OSError, AttributeError):
            return False

    def get_file_info(self, filepath: str) -> Dict[str, any]:
        """
        Get comprehensive file information for debugging.

        Args:
            filepath: Path to the script file

        Returns:
            Dictionary with file information
        """
        path = Path(filepath)
        info = {
            'filepath': str(path.absolute()),
            'exists': path.exists(),
            'size': path.stat().st_size if path.exists() else 0,
            'extension': path.suffix,
            'is_executable': self.is_executable(filepath),
            'detected_type': self.detect_type(filepath),
            'confidence_scores': self.get_confidence_scores(filepath),
        }

        # Add shebang info
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
            info['shebang'] = first_line if first_line.startswith('#!') else None
        except (IOError, UnicodeDecodeError):
            info['shebang'] = None

        return info