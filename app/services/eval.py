"""Evaluation service — LLM-as-judge to score explanation quality."""

from openai import OpenAI
import time
import structlog

from app.core.config import get_settings
from app.services.metrics_logger import log_llm_metric

logger = structlog.get_logger()

_EVAL_SYSTEM_PROMPT = """\
You are an expert evaluator of financial explanations. Rate the clarity,
accuracy, and helpfulness of a given explanation on a scale of 1 to 5:

1 = Confusing, inaccurate, or unhelpful
2 = Some useful information but with clarity issues
3 = Clear and useful explanation
4 = Very clear, accurate, and actionable
5 = Excellent explanation; concise, accurate, insightful

Respond with ONLY a single integer (1-5). No explanation needed.
"""


def score_explanation(explanation: str) -> int:
    """Score an explanation using LLM-as-judge (1-5).

    Args:
        explanation: The text explanation to evaluate.

    Returns:
        Integer score from 1 to 5.

    Raises:
        ValueError: If Groq API key is not configured.
        ValueError: If the response cannot be parsed as an integer.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = OpenAI(
        api_key=settings.groq_api_key,
        base_url="https://api.groq.com/openai/v1",
    )

    start = time.time()
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": _EVAL_SYSTEM_PROMPT},
            {"role": "user", "content": explanation},
        ],
        max_tokens=10,
        temperature=0.0,
    )
    duration = time.time() - start

    raw_score = response.choices[0].message.content.strip()

    try:
        score = int(raw_score)
        if not 1 <= score <= 5:
            raise ValueError(f"Score out of range: {score}")

        logger.info(
            "eval.score",
            score=score,
            explanation_len=len(explanation),
            model=settings.groq_model,
            duration_seconds=round(duration, 3),
        )

        log_llm_metric(
            operation="eval",
            model=settings.groq_model,
            duration_ms=duration * 1000,
            eval_score=score,
        )

        return score
    except ValueError as e:
        raise ValueError(f"Could not parse eval score '{raw_score}' as integer: {e}") from e
