from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

from app.core.config import get_settings
from app.ml.dataset import build_dataset


def train_and_save() -> None:
    """Train the risk classifier and persist artifacts to disk."""

    settings = get_settings()
    model_path = Path(settings.model_path)
    encoder_path = Path(settings.model_encoder_path)

    model_path.parent.mkdir(parents=True, exist_ok=True)

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    df = build_dataset(symbols)

    X = df[["volatility", "max_drawdown", "mean_return"]]
    y = df["label"]

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y_encoded)

    joblib.dump(model, model_path)
    joblib.dump(encoder, encoder_path)

    print(f"Model saved to {model_path}")
    print(f"Encoder saved to {encoder_path}")


if __name__ == "__main__":
    train_and_save()