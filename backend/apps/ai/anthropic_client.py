import anthropic
from django.conf import settings


class AIProviderError(Exception):
    """Raised on any failure talking to the model provider — callers map
    this to a clear error (a 502-ish API response, or an
    AiGenerationJob.status="failed" + error_message) rather than letting
    an SDK exception leak out raw."""


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise AIProviderError("ANTHROPIC_API_KEY is not configured.")
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def send_message(system: str, user_message: str, *, model: str, max_tokens: int) -> str:
    """The only place the Anthropic SDK is called — isolated here so
    tests can monkeypatch this one function instead of mocking the SDK
    client itself. Non-streaming: every caller is a single chat turn or a
    bounded content-generation job, well under the size where streaming
    is needed to avoid an HTTP timeout."""
    client = _get_client()
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
    except (anthropic.APIConnectionError, anthropic.APIStatusError) as exc:
        raise AIProviderError(f"Anthropic API call failed: {exc}") from exc

    if response.stop_reason == "refusal":
        raise AIProviderError("The model declined to respond to this request.")

    return "".join(block.text for block in response.content if block.type == "text")
