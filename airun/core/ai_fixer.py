"""
AI-powered error fixing implementation.
"""
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from .detector import ScriptType
from .runners import ExecutionResult
from .llm_router import LLMRouter, ErrorContext, CodeFix, create_error_context

logger = logging.getLogger(__name__)


@dataclass
class FixAttempt:
    """Record of a fix attempt."""
    attempt_number: int
    provider_used: str
    confidence: float
    success: bool
    error_message: Optional[str] = None
    execution_time: float = 0.0
    changes_applied: Optional[List[str]] = None


class AIFixer:
    """AI-powered error fixing engine."""

    def __init__(self, llm_router: LLMRouter, config: Any):
        """
        Initialize AI fixer.

        Args:
            llm_router: LLM router for generating fixes
            config: Configuration object
        """
        self.llm_router = llm_router
        self.config = config
        self.fix_history: List[FixAttempt] = []

        # Configuration options
        self.min_confidence_threshold = getattr(config, 'min_confidence_threshold', 0.5)
        self.max_retries = getattr(config, 'max_retries', 3)
        self.interactive_mode = getattr(config, 'interactive_mode', False)
        self.backup_enabled = getattr(config, 'backup_enabled', True)

    def fix_script_error(self, script_path: str, script_type: ScriptType,
                        execution_result: ExecutionResult,
                        provider_name: Optional[str] = None) -> bool:
        """
        Attempt to fix a script error using AI.

        Args:
            script_path: Path to the script with error
            script_type: Type of the script
            execution_result: Result of the failed execution
            provider_name: Optional specific LLM provider to use

        Returns:
            True if fix was successfully applied, False otherwise
        """
        logger.info(f"Attempting to fix error in {script_path}")

        try:
            # Read current script content
            script_content = self._read_script(script_path)
            if not script_content:
                logger.error(f"Could not read script content from {script_path}")
                return False

            # Create error context
            error_context = self._create_error_context(
                script_type=script_type,
                script_path=script_path,
                script_content=script_content,
                execution_result=execution_result
            )

            # Generate fix using LLM
            start_time = time.time()
            try:
                code_fix = self.llm_router.fix_error(error_context, provider_name)
            except Exception as e:
                logger.error(f"Failed to generate fix: {e}")
                self._record_fix_attempt(
                    provider_used=provider_name or "unknown",
                    confidence=0.0,
                    success=False,
                    error_message=str(e),
                    execution_time=time.time() - start_time
                )
                return False

            execution_time = time.time() - start_time

            # Check confidence threshold
            if code_fix.confidence < self.min_confidence_threshold:
                logger.warning(f"Fix confidence {code_fix.confidence:.2f} below threshold {self.min_confidence_threshold}")
                if not self._confirm_low_confidence_fix(code_fix):
                    self._record_fix_attempt(
                        provider_used=provider_name or "auto",
                        confidence=code_fix.confidence,
                        success=False,
                        error_message="Below confidence threshold",
                        execution_time=execution_time
                    )
                    return False

            # Interactive confirmation if enabled
            if self.interactive_mode and not self._confirm_fix_application(code_fix):
                logger.info("Fix application cancelled by user")
                return False

            # Apply the fix
            success = self._apply_fix(script_path, code_fix)

            self._record_fix_attempt(
                provider_used=provider_name or "auto",
                confidence=code_fix.confidence,
                success=success,
                execution_time=execution_time,
                changes_applied=code_fix.changes_made
            )

            if success:
                logger.info(f"Successfully applied fix to {script_path}")
                logger.debug(f"Fix explanation: {code_fix.explanation}")
            else:
                logger.error(f"Failed to apply fix to {script_path}")

            return success

        except Exception as e:
            logger.error(f"Unexpected error during fix attempt: {e}")
            return False

    def _read_script(self, script_path: str) -> Optional[str]:
        """Read script content from file."""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read script {script_path}: {e}")
            return None

    def _create_error_context(self, script_type: ScriptType, script_path: str,
                             script_content: str, execution_result: ExecutionResult) -> ErrorContext:
        """Create error context from execution result."""

        # Extract line number from error message if possible
        line_number = self._extract_line_number(execution_result.stderr)

        # Get relevant code snippet (around error line if known)
        code_snippet = self._get_relevant_code_snippet(
            script_content, line_number
        )

        return create_error_context(
            script_type=script_type,
            error_message=execution_result.stderr.strip(),
            code_snippet=code_snippet,
            file_path=script_path,
            line_number=line_number
        )

    def _extract_line_number(self, error_message: str) -> Optional[int]:
        """Extract line number from error message."""
        import re

        # Common patterns for line numbers in error messages
        patterns = [
            r'line (\d+)',
            r'File ".*", line (\d+)',
            r':(\d+):',
            r'at line (\d+)',
            r'on line (\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    def _get_relevant_code_snippet(self, script_content: str,
                                  line_number: Optional[int] = None,
                                  context_lines: int = 5) -> str:
        """Get relevant code snippet around error line."""
        lines = script_content.split('\n')

        if line_number is None:
            # If no line number, return entire script (up to reasonable limit)
            max_lines = 50
            if len(lines) <= max_lines:
                return script_content
            else:
                return '\n'.join(lines[:max_lines]) + '\n... (truncated)'

        # Get context around the error line
        start_line = max(0, line_number - context_lines - 1)
        end_line = min(len(lines), line_number + context_lines)

        snippet_lines = lines[start_line:end_line]

        # Add line numbers for context
        numbered_lines = []
        for i, line in enumerate(snippet_lines, start=start_line + 1):
            marker = ">>>" if i == line_number else "   "
            numbered_lines.append(f"{marker} {i:3d}: {line}")

        return '\n'.join(numbered_lines)

    def _confirm_low_confidence_fix(self, code_fix: CodeFix) -> bool:
        """Ask user confirmation for low confidence fixes."""
        if not self.interactive_mode:
            return False

        print(f"\n⚠️  Low confidence fix (confidence: {code_fix.confidence:.2f})")
        print(f"Explanation: {code_fix.explanation}")
        print("Changes to be made:")
        for change in code_fix.changes_made:
            print(f"  - {change}")

        response = input("\nApply this fix anyway? [y/N]: ").strip().lower()
        return response in ['y', 'yes']

    def _confirm_fix_application(self, code_fix: CodeFix) -> bool:
        """Ask user confirmation before applying fix."""
        print(f"\n🤖 AI Fix Suggestion (confidence: {code_fix.confidence:.2f})")
        print(f"Explanation: {code_fix.explanation}")
        print("Changes to be made:")
        for change in code_fix.changes_made:
            print(f"  - {change}")

        if code_fix.fixed_code:
            print("\nFixed code preview:")
            preview_lines = code_fix.fixed_code.split('\n')[:10]
            for line in preview_lines:
                print(f"  {line}")
            if len(code_fix.fixed_code.split('\n')) > 10:
                print("  ... (truncated)")

        response = input("\nApply this fix? [Y/n]: ").strip().lower()
        return response in ['', 'y', 'yes']

    def _apply_fix(self, script_path: str, code_fix: CodeFix) -> bool:
        """Apply the code fix to the script file."""
        if not code_fix.fixed_code:
            logger.error("No fixed code provided in the fix")
            return False

        try:
            # Create backup if enabled
            if self.backup_enabled:
                self._create_backup(script_path)

            # Write the fixed code
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(code_fix.fixed_code)

            logger.info(f"Applied fix to {script_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply fix to {script_path}: {e}")
            return False

    def _create_backup(self, script_path: str) -> Optional[str]:
        """Create a backup of the script before applying fix."""
        try:
            script_path_obj = Path(script_path)
            timestamp = int(time.time())
            backup_path = script_path_obj.with_suffix(
                f'.backup.{timestamp}{script_path_obj.suffix}'
            )

            # Copy original file to backup
            import shutil
            shutil.copy2(script_path, backup_path)

            logger.debug(f"Created backup: {backup_path}")
            return str(backup_path)

        except Exception as e:
            logger.warning(f"Failed to create backup for {script_path}: {e}")
            return None

    def _record_fix_attempt(self, provider_used: str, confidence: float,
                           success: bool, error_message: Optional[str] = None,
                           execution_time: float = 0.0,
                           changes_applied: Optional[List[str]] = None) -> None:
        """Record a fix attempt for analysis."""
        attempt = FixAttempt(
            attempt_number=len(self.fix_history) + 1,
            provider_used=provider_used,
            confidence=confidence,
            success=success,
            error_message=error_message,
            execution_time=execution_time,
            changes_applied=changes_applied or []
        )

        self.fix_history.append(attempt)

        # Log attempt details
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"Fix attempt #{attempt.attempt_number}: {status} "
                   f"(provider: {provider_used}, confidence: {confidence:.2f}, "
                   f"time: {execution_time:.2f}s)")

    def get_fix_statistics(self) -> Dict[str, Any]:
        """Get statistics about fix attempts."""
        if not self.fix_history:
            return {"total_attempts": 0}

        successful_fixes = [attempt for attempt in self.fix_history if attempt.success]

        stats = {
            "total_attempts": len(self.fix_history),
            "successful_fixes": len(successful_fixes),
            "success_rate": len(successful_fixes) / len(self.fix_history),
            "average_confidence": sum(attempt.confidence for attempt in self.fix_history) / len(self.fix_history),
            "average_execution_time": sum(attempt.execution_time for attempt in self.fix_history) / len(self.fix_history),
            "providers_used": list(set(attempt.provider_used for attempt in self.fix_history)),
        }

        if successful_fixes:
            stats["successful_average_confidence"] = sum(attempt.confidence for attempt in successful_fixes) / len(successful_fixes)

        return stats

    def clear_history(self) -> None:
        """Clear fix attempt history."""
        self.fix_history.clear()
        logger.debug("Cleared fix attempt history")


class FixAnalyzer:
    """Analyzes and reports on fix attempts."""

    def __init__(self, ai_fixer: AIFixer):
        """
        Initialize fix analyzer.

        Args:
            ai_fixer: AIFixer instance to analyze
        """
        self.ai_fixer = ai_fixer

    def generate_report(self) -> str:
        """Generate a detailed report of fix attempts."""
        stats = self.ai_fixer.get_fix_statistics()

        if stats["total_attempts"] == 0:
            return "No fix attempts recorded."

        report = f"""
Fix Attempts Report
==================

Total Attempts: {stats['total_attempts']}
Successful Fixes: {stats['successful_fixes']}
Success Rate: {stats['success_rate']:.1%}
Average Confidence: {stats['average_confidence']:.2f}
Average Execution Time: {stats['average_execution_time']:.2f}s

Providers Used: {', '.join(stats['providers_used'])}
"""

        if "successful_average_confidence" in stats:
            report += f"Successful Fix Avg Confidence: {stats['successful_average_confidence']:.2f}\n"

        # Add individual attempt details
        report += "\nIndividual Attempts:\n"
        report += "-" * 50 + "\n"

        for attempt in self.ai_fixer.fix_history:
            status = "✅ SUCCESS" if attempt.success else "❌ FAILED"
            report += f"#{attempt.attempt_number}: {status} | "
            report += f"Provider: {attempt.provider_used} | "
            report += f"Confidence: {attempt.confidence:.2f} | "
            report += f"Time: {attempt.execution_time:.2f}s\n"

            if attempt.error_message:
                report += f"  Error: {attempt.error_message}\n"

            if attempt.changes_applied:
                report += f"  Changes: {', '.join(attempt.changes_applied[:3])}"
                if len(attempt.changes_applied) > 3:
                    report += f" (and {len(attempt.changes_applied) - 3} more)"
                report += "\n"

            report += "\n"

        return report

    def get_recommendations(self) -> List[str]:
        """Get recommendations for improving fix success rate."""
        stats = self.ai_fixer.get_fix_statistics()
        recommendations = []

        if stats["total_attempts"] == 0:
            return ["No fix attempts to analyze yet."]

        success_rate = stats["success_rate"]
        avg_confidence = stats["average_confidence"]

        if success_rate < 0.5:
            recommendations.append("Consider using higher-quality LLM models or multiple providers")

        if avg_confidence < 0.7:
            recommendations.append("Try providing more context in error messages")
            recommendations.append("Consider using interactive mode to review fixes")

        if stats["average_execution_time"] > 30:
            recommendations.append("Consider using faster LLM providers or reducing context size")

        provider_success = {}
        for attempt in self.ai_fixer.fix_history:
            provider = attempt.provider_used
            if provider not in provider_success:
                provider_success[provider] = {"success": 0, "total": 0}
            provider_success[provider]["total"] += 1
            if attempt.success:
                provider_success[provider]["success"] += 1

        # Find best performing provider
        best_provider = None
        best_rate = 0
        for provider, data in provider_success.items():
            rate = data["success"] / data["total"]
            if rate > best_rate:
                best_rate = rate
                best_provider = provider

        if best_provider and best_rate > success_rate:
            recommendations.append(f"Consider using '{best_provider}' as primary provider (success rate: {best_rate:.1%})")

        return recommendations or ["Fix performance looks good!"]