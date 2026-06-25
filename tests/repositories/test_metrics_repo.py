from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.repositories.metrics_repo import MetricsRepository
from app.repositories.models import LLMCallMetric, RiskAnalysis


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock()


def test_save_metric_persists_and_returns_metric(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    
    result = repo.save_metric(
        operation="generate",
        model="gpt-4",
        duration_ms=150.5,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        eval_score=85,
    )

    assert isinstance(result, LLMCallMetric)
    assert result.operation == "generate"
    assert result.model == "gpt-4"
    assert result.duration_ms == 150.5
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.total_tokens == 150
    assert result.eval_score == 85
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(result)


def test_get_avg_eval_score_returns_none_when_no_data(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    mock_session.exec.return_value.first.return_value = None

    result = repo.get_avg_eval_score(days=7)

    assert result is None


def test_get_avg_eval_score_returns_computed_average(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    mock_session.exec.return_value.first.return_value = 82.5

    result = repo.get_avg_eval_score(days=7)

    assert result == 82.5


def test_get_p95_latency_ms_returns_none_when_no_data(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    mock_session.exec.return_value.all.return_value = []

    result = repo.get_p95_latency_ms(operation="generate", days=7)

    assert result is None


def test_get_p95_latency_ms_returns_p95_value(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    rows = [LLMCallMetric(duration_ms=100.0), LLMCallMetric(duration_ms=200.0)]
    mock_session.exec.return_value.all.return_value = rows

    result = repo.get_p95_latency_ms(operation="generate", days=7)

    assert result == 200.0


def test_get_p95_latency_ms_without_operation_filter(mock_session: MagicMock) -> None:
    repo = MetricsRepository(mock_session)
    rows = [LLMCallMetric(duration_ms=100.0), LLMCallMetric(duration_ms=150.0)]
    mock_session.exec.return_value.all.return_value = rows

    result = repo.get_p95_latency_ms(days=7)

    assert result == 150.0


def test_get_avg_tokens_by_model_returns_empty_when_no_data(
    mock_session: MagicMock,
) -> None:
    repo = MetricsRepository(mock_session)
    mock_session.exec.return_value.all.return_value = []

    result = repo.get_avg_tokens_by_model(days=7)

    assert result == {}


def test_get_avg_tokens_by_model_returns_aggregated_stats(
    mock_session: MagicMock,
) -> None:
    repo = MetricsRepository(mock_session)
    rows = [("gpt-4", 100.0, 50.0, 150.0), ("gpt-3.5", 80.0, 40.0, 120.0)]
    mock_session.exec.return_value.all.return_value = rows

    result = repo.get_avg_tokens_by_model(days=7)

    assert "gpt-4" in result
    assert "gpt-3.5" in result
    assert result["gpt-4"]["avg_input_tokens"] == 100.0
    assert result["gpt-4"]["avg_output_tokens"] == 50.0
    assert result["gpt-4"]["avg_total_tokens"] == 150.0


def test_get_operation_stats_returns_empty_when_no_data(
    mock_session: MagicMock,
) -> None:
    repo = MetricsRepository(mock_session)
    mock_session.exec.return_value.all.return_value = []

    result = repo.get_operation_stats(days=7)

    assert result == {}


def test_get_operation_stats_returns_stats_per_operation(
    mock_session: MagicMock,
) -> None:
    repo = MetricsRepository(mock_session)
    rows = [("generate", 150.0, 10), ("embed", 50.0, 5)]
    mock_session.exec.return_value.all.return_value = rows

    def mock_p95(*, operation: str, days: int) -> float:
        return 180.0 if operation == "generate" else 60.0

    repo.get_p95_latency_ms = mock_p95

    result = repo.get_operation_stats(days=7)

    assert "generate" in result
    assert "embed" in result
    assert result["generate"]["avg_duration_ms"] == 150.0
    assert result["generate"]["p95_duration_ms"] == 180.0
    assert result["generate"]["call_count"] == 10