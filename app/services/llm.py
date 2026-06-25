"""LLM service — generates plain-English risk explanations via Groq."""

from openai import OpenAI
import time
import structlog

from app.core.config import get_settings
from app.services.metrics_logger import log_llm_metric

logger = structlog.get_logger()

_SYSTEM_PROMPT = """\
You are a financial risk analyst assistant.
Given quantitative risk metrics for a stock, provide a clear, concise explanation
(3-5 sentences) that a non-expert investor can understand.
Focus on what the numbers mean in practical terms and what risks the investor should be aware of.
Do not recommend buying or selling. Do not repeat the raw numbers verbatim.
"""


def explain_risk(
    symbol: str,
    days: int,
    volatility: float,
    max_drawdown: float,
    mean_return: float,
    risk_level: str,
) -> str:
    """Generate a plain-English explanation of risk metrics using an LLM.

    Args:
        symbol: Asset ticker symbol.
        days: Number of trailing days the metrics cover.
        volatility: Standard deviation of daily returns.
        max_drawdown: Worst peak-to-trough decline ratio.
        mean_return: Average daily return over the period.
        risk_level: Classified risk label (LOW, MEDIUM, or HIGH).

    Returns:
        Plain-English explanation string from the LLM.

    Raises:
        ValueError: If the OpenAI API key is not configured.
        openai.OpenAIError: On API-level failures.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file to use this endpoint."
        )

    user_message = (
        f"Analyze the risk profile of {symbol} over the last {days} days.\n\n"
        f"Risk level: {risk_level}\n"
        f"Volatility (std of daily returns): {volatility:.4f}\n"
        f"Maximum drawdown: {max_drawdown:.4f}\n"
        f"Mean daily return: {mean_return:.4f}\n\n"
        "Explain what this means for an investor in plain English."
    )

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    start = time.time()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=300,
        temperature=0.4,
    )
    duration = time.time() - start

    usage = None
    try:
        usage = getattr(response, "usage", None) or response.get("usage")
    except Exception:
        usage = None

    answer = response.choices[0].message.content.strip()

    logger.info(
        "llm.explain",
        symbol=symbol,
        days=days,
        model=settings.groq_model,
        duration_seconds=round(duration, 3),
        answer_length=len(answer),
        usage=usage,
    )

    log_llm_metric(
        operation="explain",
        model=settings.groq_model,
        duration_ms=duration * 1000,
        input_tokens=usage.get("prompt_tokens") if usage else None,
        output_tokens=usage.get("completion_tokens") if usage else None,
        total_tokens=usage.get("total_tokens") if usage else None,
    )

    return answer
