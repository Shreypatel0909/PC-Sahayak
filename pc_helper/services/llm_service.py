"""Groq LLM adapter.

Preserves the original prototype's Groq integration (same SDK and error
handling) while isolating it behind a small interface so the conversation and
retrieval logic never import the vendor SDK directly. Supports both a text model
and a vision model (for screenshot troubleshooting).

The API key is read from configuration (environment / Streamlit secrets) and is
never logged.
"""
from __future__ import annotations

from typing import List, Union

from ..core.config import LLMRuntimeConfig, LLMSecrets
from ..core.logging_config import get_logger

logger = get_logger(__name__)


class LLMError(Exception):
    """User-safe LLM error (message is safe to show)."""


class LLMConfigError(LLMError):
    pass


class LLMUnavailableError(LLMError):
    pass


# Message content can be a plain string or the OpenAI-style multimodal list
# (text + image_url) used for vision requests.
Content = Union[str, List[dict]]


class GroqLLM:
    def __init__(self, secrets: LLMSecrets, runtime: LLMRuntimeConfig):
        self.secrets = secrets
        self.runtime = runtime
        self._client = None

    @property
    def is_configured(self) -> bool:
        return self.secrets.is_configured

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.is_configured:
            raise LLMConfigError(
                "Groq API key not found. Add GROQ_API_KEY to your .env file "
                "(or .streamlit/secrets.toml). Get a free key at https://console.groq.com/keys."
            )
        try:
            from groq import Groq
        except ImportError as exc:  # pragma: no cover
            raise LLMConfigError("The 'groq' package is not installed. Run: pip install -r requirements.txt") from exc
        self._client = Groq(api_key=self.secrets.api_key, timeout=self.runtime.request_timeout_seconds)
        return self._client

    def complete(self, messages: List[dict], use_vision: bool = False, json_mode: bool = False) -> str:
        """Send chat messages and return the assistant's text reply.

        ``json_mode`` asks Groq to return a valid JSON object (much more reliable
        than hoping the model emits clean JSON). If the model rejects the
        response_format parameter, we retry once without it.
        """
        client = self._get_client()
        model = self.runtime.vision_model if use_vision else self.runtime.text_model
        try:
            from groq import APIError, AuthenticationError, RateLimitError
        except ImportError:  # pragma: no cover
            APIError = AuthenticationError = RateLimitError = ()  # type: ignore

        def _call(with_json: bool):
            kwargs = dict(
                model=model,
                messages=messages,
                temperature=self.runtime.temperature,
                max_completion_tokens=self.runtime.max_tokens,
            )
            if with_json:
                kwargs["response_format"] = {"type": "json_object"}
            resp = client.chat.completions.create(**kwargs)
            return resp.choices[0].message.content or ""

        try:
            try:
                return _call(with_json=json_mode)
            except APIError:  # type: ignore[misc]
                if json_mode:  # model may not support response_format — retry plain
                    return _call(with_json=False)
                raise
        except AuthenticationError as exc:  # type: ignore[misc]
            raise LLMConfigError("Authentication failed. Check your Groq API key.") from exc
        except RateLimitError as exc:  # type: ignore[misc]
            raise LLMUnavailableError(
                "The AI service is rate-limited right now. Please wait a moment and try again."
            ) from exc
        except APIError as exc:  # type: ignore[misc]
            logger.error("Groq APIError (%s)", exc.__class__.__name__)
            raise LLMUnavailableError(
                "Groq could not process this request. The model may be unavailable or unsupported."
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM call failed: %s", exc.__class__.__name__)
            raise LLMUnavailableError("The AI service is currently unavailable. Please try again.") from exc


def build_llm(secrets: LLMSecrets, runtime: LLMRuntimeConfig) -> GroqLLM:
    return GroqLLM(secrets, runtime)
