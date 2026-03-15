"""OpenRouter API Client for Page Speed Optimization Agent.

Handles LLM API calls for AI-powered performance analysis and recommendations.
https://openrouter.ai/
"""

import json
import re
import logging
import requests
from typing import Optional, Generator, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from LLM analysis."""
    content: str
    model: str
    usage: dict
    finish_reason: str


class OpenRouterClient:
    """Client for OpenRouter API.

    Supports multiple LLM models for page speed analysis and optimization
    recommendations.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    # Available models for performance analysis
    MODELS = {
        "gemini-flash": "google/gemini-2.0-flash-001",
        "claude-sonnet": "anthropic/claude-sonnet-4-5-20250514",
        "gpt-4.1-mini": "openai/gpt-4.1-mini",
    }

    DEFAULT_MODEL = "google/gemini-2.0-flash-001"

    def __init__(self, api_key: str, default_model: Optional[str] = None):
        """Initialize the client.

        Args:
            api_key: OpenRouter API key.
            default_model: Default model to use. Falls back to DEFAULT_MODEL.
        """
        self.api_key = api_key
        self.default_model = default_model or self.DEFAULT_MODEL

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://page-speed-optimizer.local",
            "X-Title": "Page Speed Optimization Agent",
        }

    def _make_request(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> dict:
        """Make a chat completion request.

        Args:
            messages: List of message dictionaries.
            model: Model to use.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (low for factual output).
            stream: Whether to stream response.

        Returns:
            API response dictionary.

        Raises:
            requests.HTTPError: If the API returns an error status code.
        """
        url = f"{self.BASE_URL}/chat/completions"

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=180,
        )
        response.raise_for_status()

        return response.json()

    def analyze(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> LLMResponse:
        """Run analysis with system prompt and user content.

        Args:
            system_prompt: System prompt with expertise and instructions.
            user_content: User message with performance data.
            model: Model to use (defaults to self.default_model).
            max_tokens: Maximum response tokens.

        Returns:
            LLMResponse with the analysis content.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        result = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )

        choice = result.get("choices", [{}])[0]

        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=result.get("model", ""),
            usage=result.get("usage", {}),
            finish_reason=choice.get("finish_reason", ""),
        )

    def analyze_stream(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> Generator[str, None, None]:
        """Run analysis with streaming response.

        Args:
            system_prompt: System prompt.
            user_content: User message with performance data.
            model: Model to use.
            max_tokens: Maximum response tokens.

        Yields:
            Content chunks as they arrive.
        """
        url = f"{self.BASE_URL}/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "stream": True,
        }

        with requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True,
            timeout=180,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = (
                                chunk.get("choices", [{}])[0]
                                .get("delta", {})
                                .get("content", "")
                            )
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def analyze_json(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        max_tokens: int = 8192,
    ) -> tuple[Any, LLMResponse]:
        """Run analysis and parse the response as JSON.

        Calls analyze() and attempts to parse the response content as JSON.
        If direct parsing fails, tries to extract JSON from markdown code blocks
        (```json ... ``` or ``` ... ```).

        Args:
            system_prompt: System prompt with expertise and instructions.
            user_content: User message with performance data.
            model: Model to use.
            max_tokens: Maximum response tokens.

        Returns:
            Tuple of (parsed_json, llm_response). parsed_json is the
            deserialized JSON object/array. llm_response is the full
            LLMResponse for metadata access.

        Raises:
            ValueError: If no valid JSON could be extracted from the response.
        """
        llm_response = self.analyze(
            system_prompt=system_prompt,
            user_content=user_content,
            model=model,
            max_tokens=max_tokens,
        )

        content = llm_response.content.strip()

        # Attempt 1: Direct JSON parse
        try:
            parsed = json.loads(content)
            return parsed, llm_response
        except json.JSONDecodeError:
            pass

        # Attempt 2: Extract from markdown code block (```json ... ``` or ``` ... ```)
        code_block_pattern = re.compile(
            r"```(?:json)?\s*\n?(.*?)\n?\s*```",
            re.DOTALL,
        )
        matches = code_block_pattern.findall(content)
        for match in matches:
            try:
                parsed = json.loads(match.strip())
                return parsed, llm_response
            except json.JSONDecodeError:
                continue

        # Attempt 3: Find the first [ ... ] or { ... } block in the content
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start_idx = content.find(start_char)
            if start_idx == -1:
                continue
            # Find the matching closing bracket by counting nesting
            depth = 0
            for i in range(start_idx, len(content)):
                if content[i] == start_char:
                    depth += 1
                elif content[i] == end_char:
                    depth -= 1
                if depth == 0:
                    candidate = content[start_idx : i + 1]
                    try:
                        parsed = json.loads(candidate)
                        return parsed, llm_response
                    except json.JSONDecodeError:
                        break

        raise ValueError(
            f"Could not extract valid JSON from LLM response. "
            f"Response starts with: {content[:200]}"
        )

    def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection is successful.
        """
        try:
            messages = [
                {"role": "user", "content": "Say 'OK' if you can hear me."}
            ]
            result = self._make_request(
                messages=messages,
                max_tokens=10,
            )
            return "choices" in result
        except Exception as e:
            logger.warning(f"OpenRouter connection test failed: {e}")
            return False

    def get_available_models(self) -> list[str]:
        """Get list of available model IDs.

        Returns:
            List of model identifiers.
        """
        return list(self.MODELS.values())


def create_client_from_streamlit(
    default_model: Optional[str] = None,
) -> Optional[OpenRouterClient]:
    """Create OpenRouter client from Streamlit secrets, with .env fallback.

    Tries st.secrets first, then falls back to python-dotenv loading
    from a .env file. This allows the client to work both in Streamlit Cloud
    deployments and local development.

    Args:
        default_model: Optional model override.

    Returns:
        OpenRouterClient if API key is available, None otherwise.
    """
    api_key = None
    model = default_model

    # Attempt 1: Streamlit secrets
    try:
        import streamlit as st

        api_key = st.secrets.get("OPENROUTER_API_KEY")
        if not model:
            model = st.secrets.get("DEFAULT_MODEL")
    except Exception:
        pass

    # Attempt 2: .env file via python-dotenv
    if not api_key:
        try:
            from dotenv import load_dotenv
            import os

            load_dotenv()
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not model:
                model = os.getenv("DEFAULT_MODEL")
        except ImportError:
            logger.warning(
                "python-dotenv not installed. Cannot load .env file. "
                "Install with: pip install python-dotenv"
            )
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")

    if api_key:
        return OpenRouterClient(api_key, model)

    logger.warning(
        "No OPENROUTER_API_KEY found in Streamlit secrets or .env file."
    )
    return None
