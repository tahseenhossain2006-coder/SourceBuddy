import json
import logging
import time
from typing import List, Dict, Any, Optional

import requests

from .provider import LLMProvider

logger = logging.getLogger(__name__)


class OmniRouteProvider(LLMProvider):
    """
    OpenAI-compatible provider for a local OmniRoute server.

    Expected OmniRoute base URL:
        http://localhost:20128/v1

    Supports:
    - /models
    - /chat/completions
    - JSON responses
    - SSE responses
    - automatic model normalization
    - bounded request timeouts
    """

    PROVIDER_NAME = "omniroute"

    def __init__(
        self,
        api_key: Optional[str],
        base_url: str,
        default_timeout: int = 60,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_timeout = max(5, int(default_timeout))

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            }
        )

        if self.api_key:
            self.session.headers.update(
                {
                    "Authorization": f"Bearer {self.api_key}"
                }
            )

        # Do not inherit proxy settings from Windows/environment.
        self.session.trust_env = False

        # Cache discovered model IDs.
        self._model_cache: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Models
    # ------------------------------------------------------------------

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Return models exposed by OmniRoute.

        Never raises on discovery failure; callers can decide whether
        the provider is unavailable.
        """
        try:
            response = self.session.get(
                f"{self.base_url}/models",
                timeout=min(self.default_timeout, 15),
            )

            response.raise_for_status()

            data = response.json()

            models = data.get("data", [])

            if not isinstance(models, list):
                logger.warning(
                    "OmniRoute /models returned invalid data format"
                )
                return []

            self._model_cache = models

            logger.debug(
                "OmniRoute discovered %d models",
                len(models),
            )

            return models

        except requests.exceptions.Timeout:
            logger.warning(
                "OmniRoute model discovery timed out"
            )
            return []

        except requests.exceptions.RequestException as exc:
            logger.warning(
                "OmniRoute model discovery failed: %s",
                exc,
            )
            return []

        except (ValueError, TypeError) as exc:
            logger.warning(
                "OmniRoute returned invalid /models JSON: %s",
                exc,
            )
            return []

        except Exception as exc:
            logger.warning(
                "Unexpected OmniRoute list_models error: %s",
                exc,
            )
            return []

    def _discover_model_ids(self) -> List[str]:
        """
        Get model IDs from the OmniRoute server.
        """
        models = self.list_models()

        model_ids: List[str] = []

        for item in models:
            if not isinstance(item, dict):
                continue

            model_id = item.get("id")

            if isinstance(model_id, str) and model_id.strip():
                model_ids.append(model_id.strip())

        return model_ids

    def _resolve_model(self, model: Optional[str]) -> str:
        """
        Resolve SourceAI's requested model to an actual OmniRoute model ID.

        OmniRoute may expose IDs such as:

            oc/nemotron-3-ultra-free

        while SourceAI configuration may contain:

            nemotron-3-ultra-free
        """

        requested = (model or "").strip()

        available = self._discover_model_ids()

        if not available:
            if requested:
                return requested

            raise RuntimeError(
                "OmniRoute returned no models and no model was specified"
            )

        if requested:
            # Exact match.
            if requested in available:
                return requested

            # Match against the part after a provider prefix.
            for model_id in available:
                if model_id.split("/", 1)[-1] == requested:
                    return model_id

            # Match suffix.
            for model_id in available:
                if model_id.endswith(f"/{requested}"):
                    return model_id

            # If OmniRoute does not recognize the configured alias,
            # fail with useful information instead of silently choosing
            # an unrelated model.
            raise RuntimeError(
                "OmniRoute model not found: "
                f"{requested}. Available models: {available}"
            )

        # No requested model: use first available model.
        return available[0]

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json_content(data: Dict[str, Any]) -> Optional[str]:
        """
        Extract assistant content from a standard OpenAI-compatible
        JSON response.
        """
        choices = data.get("choices")

        if not isinstance(choices, list) or not choices:
            return None

        first_choice = choices[0]

        if not isinstance(first_choice, dict):
            return None

        message = first_choice.get("message")

        if isinstance(message, dict):
            content = message.get("content")

            if isinstance(content, str):
                return content

            # Some reasoning-capable servers may expose the final
            # answer through a content field nested differently.
            if content is not None:
                return str(content)

        # Some OpenAI-compatible implementations return text directly.
        text = first_choice.get("text")

        if isinstance(text, str):
            return text

        return None

    @staticmethod
    def _extract_sse_content(raw_text: str) -> str:
        """
        Extract assistant content from Server-Sent Events.

        Handles events such as:

            data: {...}

        and:

            data: [DONE]

        OmniRoute may expose reasoning_content as well. We intentionally
        ignore reasoning_content and return only assistant content.
        """
        content_parts: List[str] = []

        for raw_line in raw_text.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            if not line.startswith("data:"):
                continue

            payload = line[5:].strip()

            if not payload or payload == "[DONE]":
                continue

            try:
                event = json.loads(payload)
            except json.JSONDecodeError:
                logger.debug(
                    "Ignoring non-JSON OmniRoute SSE event"
                )
                continue

            if not isinstance(event, dict):
                continue

            choices = event.get("choices")

            if not isinstance(choices, list) or not choices:
                continue

            choice = choices[0]

            if not isinstance(choice, dict):
                continue

            delta = choice.get("delta")

            if isinstance(delta, dict):
                # IMPORTANT:
                # Do not return reasoning_content.
                piece = delta.get("content")

                if isinstance(piece, str):
                    content_parts.append(piece)

            # Some implementations may emit message content.
            message = choice.get("message")

            if isinstance(message, dict):
                piece = message.get("content")

                if isinstance(piece, str):
                    content_parts.append(piece)

        return "".join(content_parts)

    def _extract_content(
        self,
        response: requests.Response,
    ) -> str:
        """
        Extract final assistant content from either JSON or SSE.
        """

        content_type = (
            response.headers.get("Content-Type", "")
            .lower()
        )

        # SSE response.
        if (
            "text/event-stream" in content_type
            or response.text.lstrip().startswith("data:")
        ):
            content = self._extract_sse_content(response.text)

            if content:
                return content

            raise RuntimeError(
                "OmniRoute SSE response contained no assistant content"
            )

        # Normal JSON response.
        try:
            data = response.json()
        except ValueError:
            # Server may have returned SSE without a correct content type.
            content = self._extract_sse_content(response.text)

            if content:
                return content

            raise RuntimeError(
                "OmniRoute returned neither valid JSON nor readable SSE"
            )

        if not isinstance(data, dict):
            raise RuntimeError(
                "OmniRoute returned an invalid response object"
            )

        content = self._extract_json_content(data)

        if content is None:
            raise RuntimeError(
                "OmniRoute returned no assistant content"
            )

        return content

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        messages,
        model,
        temperature=0.1,
        max_tokens=1024,
        response_format=None,
        timeout_seconds=None,
    ) -> str:
        """
        Generate text through OmniRoute.
        """

        resolved_model = self._resolve_model(model)

        url = f"{self.base_url}/chat/completions"

        payload: Dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            payload["response_format"] = response_format

        timeout = (
            int(timeout_seconds)
            if timeout_seconds is not None
            else self.default_timeout
        )

        timeout = max(5, timeout)

        logger.debug(
            "OmniRoute request: model=%s timeout=%ss",
            resolved_model,
            timeout,
        )

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=timeout,
            )

            response.raise_for_status()

            content = self._extract_content(response)

            if not content.strip():
                raise RuntimeError(
                    "OmniRoute returned an empty assistant response"
                )

            return content

        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"OmniRoute timeout after {timeout}s"
            )

        except requests.exceptions.HTTPError as exc:
            status = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            server_message = ""

            if exc.response is not None:
                try:
                    server_message = exc.response.text.strip()
                except Exception:
                    server_message = ""

            if server_message:
                raise RuntimeError(
                    "OmniRoute HTTP error "
                    f"{status}: {server_message[:1000]}"
                )

            raise RuntimeError(
                f"OmniRoute HTTP error {status}: {exc}"
            )

        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"OmniRoute network request failed: {exc}"
            )

        except RuntimeError:
            raise

        except Exception as exc:
            raise RuntimeError(
                f"OmniRoute request failed: {exc}"
            )

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(
        self,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform a real inference health check.

        The check is intentionally bounded so a broken OmniRoute server
        cannot freeze SourceAI's global provider verification.
        """

        start = time.perf_counter()

        configured_model = (
            model.strip()
            if isinstance(model, str) and model.strip()
            else None
        )

        test_model = configured_model

        try:
            # Resolve before inference so model aliases such as
            # "nemotron-3-ultra-free" become:
            #
            # "oc/nemotron-3-ultra-free"
            resolved_model = self._resolve_model(test_model)

            result = self.generate(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Reply with exactly: "
                            "SOURCEAI_HEALTH_OK"
                        ),
                    }
                ],
                model=resolved_model,
                max_tokens=128,
                temperature=0.0,
                timeout_seconds=min(
                    self.default_timeout,
                    60,
                ),
            )

            latency_ms = int(
                (time.perf_counter() - start) * 1000
            )

            return {
                "connected": True,
                "provider": self.PROVIDER_NAME,
                "model": resolved_model,
                "latency_ms": latency_ms,
                "real_inference": True,
                "response": result,
            }

        except Exception as exc:
            latency_ms = int(
                (time.perf_counter() - start) * 1000
            )

            return {
                "connected": False,
                "provider": self.PROVIDER_NAME,
                "model": test_model,
                "latency_ms": latency_ms,
                "real_inference": False,
                "error": str(exc),
            }