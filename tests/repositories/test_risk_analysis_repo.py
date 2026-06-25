from unittest.mock import MagicMock

import pytest

from app.repositories.models import RiskAnalysis
from app.repositories.risk_analysis_repo import RiskAnalysisRepository


@pytest.fixture
def mock_session() -> MagicMock:
    return MagicMock()


def test_save_persists_and_returns_analysis(mock_session: MagicMock) -> None:
    repo = RiskAnalysisRepository(mock_session)
    analysis = RiskAnalysis(symbol="AAPL", risk_level="LOW")

    result = repo.save(analysis)

    assert result == analysis
    mock_session.add.assert_called_once_with(analysis)
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(analysis)


def test_get_by_symbol_returns_all_analyses(mock_session: MagicMock) -> None:
    repo = RiskAnalysisRepository(mock_session)
    analyses = [
        RiskAnalysis(symbol="AAPL", risk_level="LOW"),
        RiskAnalysis(symbol="AAPL", risk_level="MEDIUM"),
    ]
    mock_session.exec.return_value.all.return_value = analyses

    result = repo.get_by_symbol("AAPL")

    assert result == analyses
    mock_session.exec.assert_called_once()


def test_get_by_symbol_returns_empty_list_when_none_found(
    mock_session: MagicMock,
) -> None:
    repo = RiskAnalysisRepository(mock_session)
    mock_session.exec.return_value.all.return_value = []

    result = repo.get_by_symbol("NONEXISTENT")

    assert result == []


def test_search_by_embedding_returns_closest_analyses(
    mock_session: MagicMock,
) -> None:
    repo = RiskAnalysisRepository(mock_session)
    analyses = [
        RiskAnalysis(symbol="AAPL", risk_level="LOW"),
        RiskAnalysis(symbol="MSFT", risk_level="MEDIUM"),
    ]
    mock_session.exec.return_value.all.return_value = analyses

    embedding = [0.1, 0.2, 0.3]
    result = repo.search_by_embedding(embedding, limit=5)

    assert result == analyses
    mock_session.exec.assert_called_once()


def test_search_by_embedding_with_custom_limit(mock_session: MagicMock) -> None:
    repo = RiskAnalysisRepository(mock_session)
    analyses = [RiskAnalysis(symbol="AAPL", risk_level="LOW")]
    mock_session.exec.return_value.all.return_value = analyses

    embedding = [0.1, 0.2, 0.3]
    result = repo.search_by_embedding(embedding, limit=10)

    assert result == analyses
    # Verify the query was built with the custom limit
    call_args = mock_session.exec.call_args[0][0]
    assert call_args._limit_clause is not None


def test_search_by_embedding_returns_empty_when_no_matches(
    mock_session: MagicMock,
) -> None:
    repo = RiskAnalysisRepository(mock_session)
    mock_session.exec.return_value.all.return_value = []

    embedding = [0.1, 0.2, 0.3]
    result = repo.search_by_embedding(embedding, limit=5)

    assert result == []