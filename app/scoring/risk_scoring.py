def classify_risk(volatility: float, max_drawdown: float) -> str:
    """Map volatility and drawdown features to a risk label.

    Args:
        volatility: Volatility feature value.
        max_drawdown: Maximum drawdown feature value.

    Returns:
        One of ``"LOW"``, ``"MEDIUM"``, or ``"HIGH"``.
    """
    if volatility < 0.01 and max_drawdown > -0.1:
        return "LOW"
    elif volatility < 0.025 and max_drawdown > -0.2:
        return "MEDIUM"
    else:
        return "HIGH"
