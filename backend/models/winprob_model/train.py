# backend/models/train_winprob_model.py

from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import joblib


# Paths
ROOT = Path(__file__).resolve().parents[1]        # .../backend
DATA_PATH = ROOT / "data" / "play_states.csv"     # adjust if your file is named differently
MODEL_PATH = Path(__file__).resolve().parent / "winprob_model.joblib"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)

    # Make sure columns exist – adjust names if yours differ
    required_cols = [
        "quarter",
        "seconds_remaining",
        "score_diff_home",
        "home_has_ball",
        "yardline_100",
        "down",
        "ydstogo",
        "home_win",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in data: {missing}")

    return df


def train():
    df = load_data()

    feature_cols = [
        "quarter",
        "seconds_remaining",
        "score_diff_home",
        "home_has_ball",
        "yardline_100",
        "down",
        "ydstogo",
    ]

    X = df[feature_cols].copy()
    # ensure home_has_ball is numeric 0/1
    X["home_has_ball"] = X["home_has_ball"].astype(int)

    y = df["home_win"].astype(int)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)

    # quick sanity check
    val_probs = model.predict_proba(X_val)[:, 1]
    auc = roc_auc_score(y_val, val_probs)
    print(f"Validation AUC: {auc:.3f}")

    # save model
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    train()
