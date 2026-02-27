class RiskModel:
    """Wrapper for the trained estimator and label encoder."""

    def __init__(self, model, encoder):
        """Initialize a prediction wrapper.

        Args:
            model: Trained estimator implementing ``predict``.
            encoder: Fitted label encoder used for inverse transform.
        """
        self.model = model
        self.encoder = encoder

    def predict(self, features: dict) -> str:
        """Predict a human-readable risk label from numeric features.

        Args:
            features: Feature mapping with ``volatility``,
                ``max_drawdown``, and ``mean_return``.

        Returns:
            Decoded risk label.
        """
        X = [[
            features["volatility"],
            features["max_drawdown"],
            features["mean_return"]
        ]]
        y_pred = self.model.predict(X)
        return self.encoder.inverse_transform(y_pred)[0]
