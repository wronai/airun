"""
LLM Router for managing multiple AI providers.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .detector import ScriptType

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for error fixing."""
    script_type: ScriptType
    error_message: str
    code_snippet: str
    file_path: str
    line_number: Optional[int] = None
    environment_info: Optional[Dict[str, Any]] = None
    execution_args: Optional[List[str]] = None


@dataclass
class CodeFix:
    """Represents a code fix suggestion from an LLM."""
    fixed_code: str
    explanation: str
    confidence: float
    changes_made: List[str]
    alternative_fixes: Optional[List[str]] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the LLM provider.

        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.name = self.__class__.__name__.lower().replace('provider', '')

    @abstractmethod
    def generate_fix(self, error_context: ErrorContext) -> CodeFix:
        """
        Generate a code fix for the given error context.

        Args:
            error_context: Information about the error and code

        Returns:
            CodeFix with suggested solution
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.

        Returns:
            True if provider can be used
        """
        pass

    def get_model_for_language(self, script_type: ScriptType) -> str:
        """
        Get the appropriate model for a given script type.

        Args:
            script_type: Type of script being processed

        Returns:
            Model name/identifier
        """
        models = self.config.get('models', {})
        return models.get(script_type.value, models.get('default', 'default'))

    def build_prompt(self, error_context: ErrorContext) -> str:
        """
        Build a prompt for the LLM based on error context.

        Args:
            error_context: Error context information

        Returns:
            Formatted prompt string
        """
        language = error_context.script_type.value

        prompt = f"""Fix this {language} code error:

Error: {error_context.error_message}
File: {error_context.file_path}"""

        if error_context.line_number:
            prompt += f"\nLine: {error_context.line_number}"

        prompt += f"""

Code:
```{language}
{error_context.code_snippet}
```

Please provide:
1. The corrected code
2. Explanation of what was wrong
3. Summary of changes made

Format your response as:
FIXED_CODE:
```{language}
[corrected code here]
```

EXPLANATION:
[explanation of the fix]

CHANGES:
- [change 1]
- [change 2]
"""
        return prompt


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 30)

    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def generate_fix(self, error_context: ErrorContext) -> CodeFix:
        """Generate fix using Ollama."""
        if not self.is_available():
            raise RuntimeError("Ollama service is not available")

        import requests

        model = self.get_model_for_language(error_context.script_type)
        prompt = self.build_prompt(error_context)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return self._parse_response(result.get('response', ''))
            else:
                raise RuntimeError(f"Ollama API error: {response.status_code}")

        except requests.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}")

    def _parse_response(self, response: str) -> CodeFix:
        """Parse Ollama response into CodeFix."""
        fixed_code = ""
        explanation = ""
        changes = []

        # Extract fixed code
        if "FIXED_CODE:" in response:
            code_start = response.find("```", response.find("FIXED_CODE:"))
            if code_start != -1:
                code_start = response.find("\n", code_start) + 1
                code_end = response.find("```", code_start)
                if code_end != -1:
                    fixed_code = response[code_start:code_end].strip()

        # Extract explanation
        if "EXPLANATION:" in response:
            exp_start = response.find("EXPLANATION:") + len("EXPLANATION:")
            exp_end = response.find("CHANGES:")
            if exp_end == -1:
                exp_end = len(response)
            explanation = response[exp_start:exp_end].strip()

        # Extract changes
        if "CHANGES:" in response:
            changes_section = response[response.find("CHANGES:"):]
            changes = [
                line.strip().lstrip('- ')
                for line in changes_section.split('\n')
                if line.strip().startswith('-')
            ]

        confidence = 0.8 if fixed_code else 0.1

        return CodeFix(
            fixed_code=fixed_code,
            explanation=explanation,
            confidence=confidence,
            changes_made=changes
        )


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'gpt-4')
        self.timeout = config.get('timeout', 30)

    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        if not self.api_key:
            return False

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            # Try a simple completion to test API
            client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.debug(f"OpenAI not available: {e}")
            return False

    def generate_fix(self, error_context: ErrorContext) -> CodeFix:
        """Generate fix using OpenAI."""
        if not self.is_available():
            raise RuntimeError("OpenAI API is not available")

        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)

            prompt = self.build_prompt(error_context)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert programmer who fixes code errors."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            return self._parse_response(content)

        except Exception as e:
            raise RuntimeError(f"OpenAI request failed: {e}")

    def _parse_response(self, response: str) -> CodeFix:
        """Parse OpenAI response into CodeFix."""
        # Similar parsing logic as Ollama
        # Implementation would be similar to OllamaProvider._parse_response
        return CodeFix(
            fixed_code=response,
            explanation="OpenAI fix applied",
            confidence=0.9,
            changes_made=["Applied OpenAI suggestion"]
        )


class ClaudeProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        self.timeout = config.get('timeout', 30)

    def is_available(self) -> bool:
        """Check if Claude API is available."""
        if not self.api_key:
            return False

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            # Test API availability
            client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            logger.debug(f"Claude not available: {e}")
            return False

    def generate_fix(self, error_context: ErrorContext) -> CodeFix:
        """Generate fix using Claude."""
        if not self.is_available():
            raise RuntimeError("Claude API is not available")

        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)

            prompt = self.build_prompt(error_context)

            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            return self._parse_response(content)

        except Exception as e:
            raise RuntimeError(f"Claude request failed: {e}")

    def _parse_response(self, response: str) -> CodeFix:
        """Parse Claude response into CodeFix."""
        # Similar parsing logic as Ollama
        return CodeFix(
            fixed_code=response,
            explanation="Claude fix applied",
            confidence=0.9,
            changes_made=["Applied Claude suggestion"]
        )


class LLMRouter:
    """Routes requests to appropriate LLM providers."""

    def __init__(self, config: Any):
        """
        Initialize LLM router with configuration.

        Args:
            config: Configuration object containing LLM provider settings
        """
        self.config = config
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize available LLM providers."""
        provider_configs = getattr(self.config, 'llm_providers', {})

        # Initialize Ollama provider
        if 'ollama' in provider_configs:
            try:
                self.providers['ollama'] = OllamaProvider(provider_configs['ollama'])
                logger.debug("Initialized Ollama provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama provider: {e}")

        # Initialize OpenAI provider
        if 'openai' in provider_configs:
            try:
                self.providers['openai'] = OpenAIProvider(provider_configs['openai'])
                logger.debug("Initialized OpenAI provider")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")

        # Initialize Claude provider
        if 'claude' in provider_configs or 'anthropic' in provider_configs:
            try:
                claude_config = provider_configs.get('claude', provider_configs.get('anthropic', {}))
                self.providers['claude'] = ClaudeProvider(claude_config)
                logger.debug("Initialized Claude provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Claude provider: {e}")

    def get_provider(self, provider_name: Optional[str] = None) -> LLMProvider:
        """
        Get a specific LLM provider.

        Args:
            provider_name: Name of the provider. If None, uses default.

        Returns:
            LLM provider instance

        Raises:
            ValueError: If provider not found or not available
        """
        if provider_name is None:
            # Use default provider from config
            default_llm = getattr(self.config, 'default_llm', 'ollama:codellama')
            provider_name = default_llm.split(':')[0]

        if provider_name not in self.providers:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

        provider = self.providers[provider_name]
        if not provider.is_available():
            raise ValueError(f"LLM provider '{provider_name}' is not available")

        return provider

    def get_available_providers(self) -> List[str]:
        """
        Get list of available LLM providers.

        Returns:
            List of provider names that are currently available
        """
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        return available

    def fix_error(self, error_context: ErrorContext,
                  provider_name: Optional[str] = None) -> CodeFix:
        """
        Fix an error using the specified or default LLM provider.

        Args:
            error_context: Context information about the error
            provider_name: Optional provider to use

        Returns:
            Code fix suggestion

        Raises:
            RuntimeError: If no providers are available or fix fails
        """
        try:
            provider = self.get_provider(provider_name)
            logger.info(f"Using {provider.name} to fix {error_context.script_type.value} error")

            fix = provider.generate_fix(error_context)

            logger.info(f"Generated fix with confidence {fix.confidence:.2f}")
            return fix

        except ValueError as e:
            # Try fallback providers
            available_providers = self.get_available_providers()
            if not available_providers:
                raise RuntimeError("No LLM providers are available")

            logger.warning(f"Primary provider failed: {e}. Trying fallback providers.")

            for fallback_provider in available_providers:
                try:
                    provider = self.get_provider(fallback_provider)
                    fix = provider.generate_fix(error_context)
                    logger.info(f"Fallback provider {fallback_provider} succeeded")
                    return fix
                except Exception as fallback_error:
                    logger.debug(f"Fallback provider {fallback_provider} failed: {fallback_error}")
                    continue

            raise RuntimeError("All LLM providers failed to generate a fix")

    def test_providers(self) -> Dict[str, bool]:
        """
        Test all configured providers.

        Returns:
            Dictionary mapping provider names to availability status
        """
        results = {}
        for name, provider in self.providers.items():
            try:
                results[name] = provider.is_available()
            except Exception:
                results[name] = False
        return results

    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all providers.

        Returns:
            Dictionary with provider information
        """
        info = {}
        for name, provider in self.providers.items():
            info[name] = {
                'available': provider.is_available(),
                'config_keys': list(provider.config.keys()),
                'models': provider.config.get('models', {}),
                'class': provider.__class__.__name__
            }
        return info

    def validate_configuration(self) -> List[str]:
        """
        Validate provider configurations.

        Returns:
            List of validation errors (empty if all valid)
        """
        errors = []

        for name, provider in self.providers.items():
            try:
                if not provider.is_available():
                    errors.append(f"Provider '{name}' is not available")
            except Exception as e:
                errors.append(f"Provider '{name}' configuration error: {e}")

        if not self.providers:
            errors.append("No LLM providers configured")

        # Check default provider
        try:
            default_llm = getattr(self.config, 'default_llm', '')
            if default_llm:
                default_provider = default_llm.split(':')[0]
                if default_provider not in self.providers:
                    errors.append(f"Default provider '{default_provider}' not configured")
        except Exception as e:
            errors.append(f"Invalid default_llm configuration: {e}")

        return errors


def create_error_context(script_type: ScriptType, error_message: str,
                        code_snippet: str, file_path: str,
                        line_number: Optional[int] = None,
                        execution_args: Optional[List[str]] = None) -> ErrorContext:
    """
    Convenience function to create ErrorContext.

    Args:
        script_type: Type of script that had the error
        error_message: The error message
        code_snippet: Relevant code snippet
        file_path: Path to the script file
        line_number: Optional line number where error occurred
        execution_args: Optional execution arguments

    Returns:
        ErrorContext instance
    """
    import os
    import platform

    # Gather environment information
    env_info = {
        'os': platform.system(),
        'python_version': platform.python_version(),
        'working_directory': os.getcwd(),
        'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
    }

    return ErrorContext(
        script_type=script_type,
        error_message=error_message,
        code_snippet=code_snippet,
        file_path=file_path,
        line_number=line_number,
        environment_info=env_info,
        execution_args=execution_args
    )