"""Central LLM factory — Groq + Google only (fast, low-latency providers).

Routing (Groq's free tier caps output at ~1000 tokens/min, so heavy
evaluation calls default to Gemini which has far higher limits):

    light calls (resume structuring)  -> LLM_PROVIDER (default: groq)
    heavy calls (repo evaluation)     -> LLM_HEAVY_PROVIDER (default: google)

Override via env:
    LLM_PROVIDER=groq|google         (default: groq)
    LLM_MODEL=<model id>             (default per provider)
    LLM_HEAVY_PROVIDER=groq|google   (default: google)
    LLM_HEAVY_MODEL=<model id>       (default per heavy provider)
    GROQ_API_KEY / GOOGLE_API_KEY
    LLM_BASE_URL                     (advanced override, applies to both)
    LLM_TIMEOUT                      (seconds, default 60)
    LLM_RETRIES                      (rate-limit retries, default 3)

chat_completion() also fails over to the OTHER provider automatically on
rate-limit / request-too-large errors, so one provider's quota can never
kill a run while the other key is configured.
"""

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

GROQ_DEFAULT_MODEL = "qwen/qwen3.8-27b"  # verified via Groq API
GOOGLE_DEFAULT_MODEL = "gemini-3.5-flash-lite"  # verified via Google OpenAI-compat endpoint

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GOOGLE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def _model_for(provider: str, task: str) -> str:
    """LLM_HEAVY_MODEL wins for heavy tasks, else LLM_MODEL, else default."""
    if task == "heavy" and os.environ.get("LLM_HEAVY_MODEL"):
        return os.environ["LLM_HEAVY_MODEL"]
    if os.environ.get("LLM_MODEL"):
        return os.environ["LLM_MODEL"]
    return GOOGLE_DEFAULT_MODEL if provider == "google" else GROQ_DEFAULT_MODEL


def _config_for(provider: str, task: str = "default") -> tuple[str, str, str]:
    """Return (base_url, api_key, model) for a provider. Raises RuntimeError."""
    provider = provider.lower()
    if provider == "google":
        base_url = os.environ.get("LLM_BASE_URL", GOOGLE_BASE_URL)
        api_key = os.environ.get("GOOGLE_API_KEY", "")
    elif provider == "groq":
        base_url = os.environ.get("LLM_BASE_URL", GROQ_BASE_URL)
        api_key = os.environ.get("GROQ_API_KEY", "")
    else:
        raise RuntimeError(
            f"Unknown LLM provider '{provider}'. Use groq|google."
        )
    if not api_key:
        need = "GOOGLE_API_KEY" if provider == "google" else "GROQ_API_KEY"
        raise RuntimeError(
            f"Missing API key for LLM provider '{provider}'. Set {need} in .env."
        )
    return base_url, api_key, _model_for(provider, task)


def get_llm_config(task: str = "default") -> tuple[str, str, str]:
    """Return (base_url, api_key, model).

    task="heavy" (repo evaluation, crew) -> LLM_HEAVY_PROVIDER (default google).
    anything else (resume parsing)       -> LLM_PROVIDER (default groq).
    Falls back to whichever provider has a key if the preferred one is
    unconfigured, so single-key setups keep working.
    """
    if task == "heavy":
        preferred = os.environ.get("LLM_HEAVY_PROVIDER", "google").lower()
        fallback = os.environ.get("LLM_PROVIDER", "groq").lower()
    else:
        preferred = os.environ.get("LLM_PROVIDER", "groq").lower()
        fallback = os.environ.get("LLM_HEAVY_PROVIDER", "google").lower()
    try:
        return _config_for(preferred, task)
    except RuntimeError:
        if fallback == preferred:
            raise
        return _config_for(fallback, task)


def get_llm_client(task: str = "default") -> tuple[OpenAI, str]:
    """Return (OpenAI-compatible client, model id) for a task class."""
    base_url, api_key, model = get_llm_config(task)
    timeout = float(os.environ.get("LLM_TIMEOUT", "60"))
    return OpenAI(base_url=base_url, api_key=api_key, timeout=timeout), model


def _is_quota_error(msg: str) -> bool:
    m = msg.lower()
    return (
        "429" in msg
        or "rate_limit" in m
        or "rate limit" in m
        or "request too large" in m
        or "output tokens" in m
    )


def _is_retryable(msg: str) -> bool:
    m = msg.lower()
    if _is_quota_error(msg):
        return True
    return any(
        s in m
        for s in (
            "500", "502", "503", "504",
            "overloaded", "unavailable", "temporarily",
            "timeout", "timed out", "connection",
            "server error", "internal error", "try again later",
        )
    )


def _alternate_config(base_url: str) -> tuple[str, str, str] | None:
    """Config for the OTHER provider (Groq<->Google), or None if unkeyed."""
    want = "google" if "groq" in base_url else "groq"
    try:
        return _config_for(want)
    except RuntimeError:
        return None


def chat_completion(client: OpenAI, model: str, _failover_done: bool = False, **kwargs):
    """chat.completions.create with retries + cross-provider failover.

    - Retryable errors (429/rate-limit/request-too-large markers, 5xx,
      overloaded/UNAVAILABLE, timeouts): back off — provider's `try again
      in Ns` hint when present, else 15s (capped 90s) — up to LLM_RETRIES.
    - request-too-large skips waiting (retrying won't heal it).
    - When retries exhaust and the OTHER provider has a key, fail over to
      it (one level only). This is what saves heavy Groq calls that exceed
      its ~1000 output-tokens/min ceiling — they transparently move to
      Gemini — and vice versa when Gemini 503s under load.
    - Non-retryable 4xx (400/401/404) raise immediately.
    """
    import re
    import time

    retries = int(os.environ.get("LLM_RETRIES", "3"))
    last_err = None
    for attempt in range(retries + 1):
        try:
            return client.chat.completions.create(model=model, **kwargs)
        except Exception as e:
            last_err = e
            msg = str(e)
            if not _is_retryable(msg):
                raise
            if attempt >= retries:
                break
            m = re.search(r"try again in (\d+)s", msg)
            # request-too-large won't heal by waiting — fail over fast.
            if "too large" in msg.lower() or "output tokens" in msg.lower():
                break
            time.sleep(min(int(m.group(1)) + 2 if m else 15, 90))

    if _failover_done:
        raise last_err
    failover = _alternate_config(str(getattr(client, "base_url", "")))
    if failover is not None:
        base_url, api_key, fb_model = failover
        timeout = float(os.environ.get("LLM_TIMEOUT", "60"))
        fb_client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        # One level only: retries apply, but no further failover (no ping-pong).
        return chat_completion(fb_client, fb_model, _failover_done=True, **kwargs)
    raise last_err
