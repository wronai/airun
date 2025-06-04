"""
Batch execution utility (minimal implementation).
"""
from typing import List
from airun.core.runners import ExecutionResult

class BatchExecutor:
    """Executes multiple scripts in batch."""

    def execute_batch(self, script_paths: List[str], parallel: bool = False,
                     stop_on_error: bool = False) -> List[ExecutionResult]:
        """Execute multiple scripts."""
        import click
        click.echo("⚠️  Batch execution feature coming in future release!")

        # Return mock results for now
        return [ExecutionResult(0, f"Would execute: {path}", "", 0.1)
                for path in script_paths]

    def generate_report(self, results: List[ExecutionResult], output_path: str):
        """Generate batch execution report."""
        with open(output_path, 'w') as f:
            f.write("Batch Execution Report\n")
            f.write("=" * 50 + "\n")
            f.write("⚠️  Full reporting feature coming soon!\n")

