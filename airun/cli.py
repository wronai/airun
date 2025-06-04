"""
Command Line Interface for AIRun.
"""
import sys
import os
import click
from pathlib import Path
from typing import Optional, List
import time

from .core.detector import ScriptDetector, ScriptType
from .core.runners import RunnerFactory, ExecutionContext
from .core.config import Config
from .core.llm_router import LLMRouter
from .utils.logging import setup_logging, get_logger
from .utils.validation import validate_script_path, validate_llm_provider


logger = get_logger(__name__)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.pass_context
def cli(ctx, version):
    """AIRun - AI-Enhanced Universal Script Runner with automatic error fixing."""
    if version:
        from . import __version__
        click.echo(f"AIRun version {__version__}")
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.option('--lang', 'language',
              type=click.Choice(['python', 'shell', 'nodejs', 'php']),
              help='Force specific language interpreter')
@click.option('--llm', 'llm_provider',
              help='LLM provider (e.g., ollama:codellama, openai:gpt-4)')
@click.option('--no-fix', is_flag=True,
              help='Disable automatic error fixing')
@click.option('--interactive', is_flag=True,
              help='Enable interactive mode for fixes')
@click.option('--max-retries', type=int, default=3,
              help='Maximum number of fix attempts')
@click.option('--config', 'config_path', type=click.Path(),
              help='Path to configuration file')
@click.option('--dry-run', is_flag=True,
              help='Validate and analyze without execution')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose output')
@click.option('--timeout', type=int,
              help='Execution timeout in seconds')
@click.argument('script_args', nargs=-1)
def run(script_path: str, language: Optional[str], llm_provider: Optional[str],
        no_fix: bool, interactive: bool, max_retries: int,
        config_path: Optional[str], dry_run: bool, verbose: bool,
        timeout: Optional[int], script_args: tuple):
    """
    Execute a script with AI-enhanced error fixing.

    SCRIPT_PATH: Path to the script to execute
    SCRIPT_ARGS: Arguments to pass to the script
    """
    # Setup logging
    setup_logging(verbose=verbose)

    try:
        # Load configuration
        config = Config.load(config_path)

        # Override config with CLI options
        if no_fix:
            config.auto_fix = False
        if interactive:
            config.interactive_mode = True
        if llm_provider:
            if not validate_llm_provider(llm_provider):
                raise click.BadParameter(f"Invalid LLM provider format: {llm_provider}")
            config.default_llm = llm_provider
        if timeout:
            config.timeout = timeout

        # Validate script path
        script_path = validate_script_path(script_path)

        # Detect script type
        detector = ScriptDetector()
        if language:
            script_type = ScriptType(language)
            logger.info(f"Forced language: {script_type.value}")
        else:
            script_type = detector.detect_type(script_path)
            logger.info(f"Detected language: {script_type.value}")

        if script_type == ScriptType.UNKNOWN:
            click.echo("❌ Unable to determine script type", err=True)
            click.echo("Try using --lang to specify the language explicitly", err=True)
            sys.exit(1)

        # Create runner
        try:
            runner = RunnerFactory.create_runner(script_type, config.runners)
        except ValueError as e:
            click.echo(f"❌ {e}", err=True)
            sys.exit(1)

        # Validate executable availability
        if not runner.validate_executable():
            executable = runner.get_executable()
            click.echo(f"❌ Required executable '{executable}' not found", err=True)
            click.echo(f"Please install {script_type.value} interpreter", err=True)
            sys.exit(1)

        # Dry run mode
        if dry_run:
            perform_dry_run(script_path, script_type, runner, detector)
            return

        # Initialize LLM router if fixing is enabled
        llm_router = None
        if config.auto_fix:
            try:
                llm_router = LLMRouter(config)
                logger.info(f"Using LLM provider: {config.default_llm}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM: {e}")
                if interactive:
                    if not click.confirm("Continue without AI fixing?"):
                        sys.exit(1)
                config.auto_fix = False

        # Execute script
        click.echo(f"🚀 Executing {script_path} ({script_type.value})")

        result = execute_with_fixing(
            script_path=script_path,
            script_type=script_type,
            runner=runner,
            llm_router=llm_router,
            config=config,
            args=list(script_args),
            max_retries=max_retries
        )

        # Output results
        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, file=sys.stderr, nl=False)

        # Status summary
        status_emoji = "✅" if not result.error_detected else "❌"
        click.echo(f"\n{status_emoji} Execution completed in {result.execution_time:.2f}s")

        sys.exit(result.exit_code)

    except KeyboardInterrupt:
        click.echo("\n⚠️ Execution interrupted by user", err=True)
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=verbose)
        click.echo(f"❌ {e}", err=True)
        sys.exit(1)


def perform_dry_run(script_path: str, script_type: ScriptType, runner, detector):
    """Perform dry run analysis without execution."""
    click.echo("🔍 Dry run analysis")
    click.echo("=" * 50)

    # File information
    file_info = detector.get_file_info(script_path)
    click.echo(f"📁 File: {file_info['filepath']}")
    click.echo(f"📏 Size: {file_info['size']} bytes")
    click.echo(f"🔧 Executable: {file_info['is_executable']}")
    click.echo(f"🏷️  Detected type: {file_info['detected_type'].value}")

    if file_info['shebang']:
        click.echo(f"#!/ Shebang: {file_info['shebang']}")

    # Confidence scores
    click.echo("\n📊 Detection confidence:")
    for script_type_enum, score in file_info['confidence_scores'].items():
        if score > 0:
            click.echo(f"  {script_type_enum.value}: {score:.2f}")

    # Syntax validation
    click.echo(f"\n🔍 Syntax validation ({script_type.value}):")
    if hasattr(runner, 'validate_syntax'):
        syntax_error = runner.validate_syntax(script_path)
        if syntax_error:
            click.echo(f"❌ {syntax_error}")
        else:
            click.echo("✅ Syntax is valid")
    else:
        click.echo("⚠️ Syntax validation not supported for this language")

    # Executable check
    click.echo(f"\n🛠️ Runtime availability:")
    executable = runner.get_executable()
    available = runner.validate_executable()
    status = "✅ Available" if available else "❌ Not found"
    click.echo(f"  {executable}: {status}")

    click.echo(f"\n📋 Would execute: {' '.join(runner.get_command(script_path))}")


def execute_with_fixing(script_path: str, script_type: ScriptType, runner,
                       llm_router, config, args: List[str], max_retries: int):
    """Execute script with AI fixing logic."""
    from .core.ai_fixer import AIFixer

    if not config.auto_fix or not llm_router:
        # Simple execution without fixing
        return runner.execute(script_path, args)

    ai_fixer = AIFixer(llm_router, config)

    with ExecutionContext(script_path, runner, backup_original=True) as ctx:
        for attempt in range(max_retries + 1):
            if attempt > 0:
                click.echo(f"🔄 Retry attempt {attempt}/{max_retries}")

            result = ctx.execute(args)

            if not result.error_detected:
                if attempt > 0:
                    click.echo("✅ Error fixed successfully!")
                return result

            if attempt < max_retries:
                click.echo(f"❌ Error detected: {result.stderr.strip()}")

                if config.interactive_mode:
                    if not click.confirm("Attempt AI fix?"):
                        break

                click.echo("🤖 Attempting AI fix...")

                try:
                    success = ai_fixer.fix_script_error(
                        script_path=script_path,
                        script_type=script_type,
                        execution_result=result
                    )

                    if success:
                        click.echo("🔧 Applied AI fix, retrying...")
                        time.sleep(0.5)  # Brief pause before retry
                        continue
                    else:
                        click.echo("⚠️ AI fix failed")

                except Exception as e:
                    logger.error(f"AI fixing error: {e}")
                    click.echo(f"⚠️ AI fix error: {e}")

            break

    return result


@cli.command()
@click.option('--config', 'config_path', type=click.Path(),
              help='Path to configuration file')
def doctor(config_path: Optional[str]):
    """Diagnose AIRun installation and configuration."""
    click.echo("🩺 AIRun System Diagnosis")
    click.echo("=" * 50)

    try:
        # Load configuration
        config = Config.load(config_path)
        click.echo("✅ Configuration loaded successfully")

        if config_path:
            click.echo(f"📁 Config file: {config_path}")
        else:
            click.echo(f"📁 Default config location: {Config.get_default_config_path()}")

    except Exception as e:
        click.echo(f"❌ Configuration error: {e}")
        return

    # Check executables
    click.echo("\n🛠️ Checking interpreters:")
    validation_results = RunnerFactory.validate_all_executables(config.runners)

    for script_type, available in validation_results.items():
        runner = RunnerFactory.create_runner(script_type, config.runners)
        executable = runner.get_executable()
        status = "✅" if available else "❌"
        click.echo(f"  {script_type.value}: {executable} {status}")

    # Check LLM providers
    click.echo("\n🤖 Checking LLM providers:")
    try:
        llm_router = LLMRouter(config)

        for provider_name in config.llm_providers.keys():
            try:
                provider = llm_router.get_provider(provider_name)
                # Test basic connectivity
                status = "✅ Available"
                click.echo(f"  {provider_name}: {status}")
            except Exception as e:
                click.echo(f"  {provider_name}: ❌ {e}")

    except Exception as e:
        click.echo(f"❌ LLM router error: {e}")

    # Check directories
    click.echo("\n📁 Checking directories:")
    directories = [
        ("Config", Path.home() / ".airun"),
        ("Logs", Path.home() / ".airun" / "logs"),
        ("Backups", Path.home() / ".airun" / "backups"),
        ("Cache", Path.home() / ".airun" / "cache"),
    ]

    for name, path in directories:
        exists = path.exists()
        writable = path.is_dir() and os.access(path, os.W_OK) if exists else False
        status = "✅" if exists and writable else "❌" if exists else "⚠️"
        click.echo(f"  {name}: {path} {status}")

        if not exists:
            try:
                path.mkdir(parents=True, exist_ok=True)
                click.echo(f"    Created directory: {path}")
            except Exception as e:
                click.echo(f"    Failed to create: {e}")

    click.echo("\n📊 Summary:")
    working_interpreters = sum(1 for available in validation_results.values() if available)
    total_interpreters = len(validation_results)

    click.echo(f"  Interpreters: {working_interpreters}/{total_interpreters} working")

    if working_interpreters == 0:
        click.echo("⚠️ No interpreters available - install Python, Node.js, PHP, or Bash")
    elif working_interpreters < total_interpreters:
        click.echo("ℹ️ Some interpreters missing - install as needed")
    else:
        click.echo("✅ All core functionality available")


@cli.command('config')
@click.option('--init', is_flag=True, help='Initialize default configuration')
@click.option('--edit', is_flag=True, help='Edit configuration file')
@click.option('--show', is_flag=True, help='Show current configuration')
@click.option('--set', 'set_values', multiple=True, metavar='KEY=VALUE',
              help='Set configuration values')
def config_command(init: bool, edit: bool, show: bool, set_values: tuple):
    """Manage AIRun configuration."""
    config_path = Config.get_default_config_path()

    if init:
        if config_path.exists():
            if not click.confirm(f"Configuration file exists at {config_path}. Overwrite?"):
                return

        try:
            Config.create_default_config()
            click.echo(f"✅ Created default configuration at {config_path}")
        except Exception as e:
            click.echo(f"❌ Failed to create configuration: {e}", err=True)
            sys.exit(1)

    elif edit:
        editor = os.environ.get('EDITOR', 'nano')
        try:
            os.system(f"{editor} {config_path}")
        except Exception as e:
            click.echo(f"❌ Failed to open editor: {e}", err=True)

    elif show:
        try:
            config = Config.load()
            click.echo("📋 Current configuration:")
            click.echo("=" * 30)
            # Display configuration in a readable format
            click.echo(config.to_yaml())
        except Exception as e:
            click.echo(f"❌ Failed to load configuration: {e}", err=True)

    elif set_values:
        try:
            config = Config.load()

            for value in set_values:
                if '=' not in value:
                    click.echo(f"❌ Invalid format: {value}. Use KEY=VALUE", err=True)
                    continue

                key, val = value.split('=', 1)
                config.set_value(key, val)
                click.echo(f"✅ Set {key} = {val}")

            config.save()
            click.echo("💾 Configuration saved")

        except Exception as