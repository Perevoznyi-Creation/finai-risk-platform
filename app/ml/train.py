from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from app.ml.dataset import build_dataset

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

df = build_dataset(symbols)

X = df[["volatility", "max_drawdown", "mean_return"]]
y = df["label"]

encoder = LabelEncoder()
y_encoded = encoder.fit_transform(y)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y_encoded)

print("Model trained successfully.")