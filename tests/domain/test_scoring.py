import pytest

from app.domain.scoring import classify_risk


@pytest.mark.parametrize(
    "volatility, max_drawdown, expected",
    [
        (0.005, -0.05, "LOW"),
        (0.009, -0.09, "LOW"),
        (0.015, -0.15, "MEDIUM"),
        (0.024, -0.19, "MEDIUM"),
        (0.03, -0.25, "HIGH"),
        (0.05, -0.3, "HIGH"),
        (0.01, -0.05, "MEDIUM"),
        (0.025, -0.15, "HIGH"),
    ],
)
def test_classify_risk_returns_expected_level(
    volatility: float,
    max_drawdown: float,
    expected: str,
) -> None:
    assert classify_risk(volatility, max_drawdown) == expected


def test_classify_risk_low_threshold() -> None:
    assert classify_risk(0.009, -0.05) == "LOW"


def test_classify_risk_medium_threshold() -> None:
    assert classify_risk(0.015, -0.15) == "MEDIUM"


def test_classify_risk_high_threshold() -> None:
    assert classify_risk(0.03, -0.25) == "HIGH"


def test_classify_risk_boundary_low_to_medium() -> None:
    assert classify_risk(0.01, -0.05) == "MEDIUM"


def test_classify_risk_boundary_medium_to_high() -> None:
    assert classify_risk(0.025, -0.15) == "HIGH"