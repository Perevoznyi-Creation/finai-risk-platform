def classify_risk(volatility: float, max_drawdown: float) -> str:
    """Classify risk level based on volatility and maximum drawdown.

    This function uses simple thresholds to classify the risk level of
    an asset. The thresholds are defined as follows:
    - LOW Risk: Volatility < 0.01 and Max Drawdown > -0.1
    - MEDIUM Risk: Volatility < 0.025 and Max Drawdown > -0.2
    - HIGH Risk: All other cases

    Parameters:
        volatility (float): Annualized volatility of the asset.
        max_drawdown (float): Maximum drawdown of the asset.

    Returns:
        str: Risk classification ("Low", "Medium", "High").
    """
    if volatility < 0.01 and max_drawdown > -0.1:
        return "LOW"
    elif volatility < 0.025 and max_drawdown > -0.2:
        return "MEDIUM"
    else:
        return "HIGH"