import os
from typing import Dict, Any

import joblib
import pandas as pd

MODEL_PATH = "backend/models/ingame_model.pkl"
_STATE_FEATURES_CACHE = None  # (model, feature_cols)


def _load_model_and_features():
    """
    Load the trained in-game model and feature columns from disk.
    Use a simple module-level cache so we only load once per process.
    """
    global _STATE_FEATURES_CACHE

    if _STATE_FEATURES_CACHE is not None:
        return _STATE_FEATURES_CACHE

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

    print(f"Loading in-game model from {MODEL_PATH} ...")
    bundle = joblib.load(MODEL_PATH)

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]

    _STATE_FEATURES_CACHE = (model, feature_cols)
    print("Model loaded.")
    return _STATE_FEATURES_CACHE


def predict_home_win_prob(state: Dict[str, Any]) -> float:
    """
    Given a dict describing the current game state from the home team's perspective,
    return the model's probability that the home team wins the game.

    Expected keys in `state` (same as feature_cols used in training):
        - season
        - week
        - quarter
        - seconds_remaining
        - score_diff_home
        - home_has_ball
        - yardline_100
        - down
        - ydstogo

    Any missing keys will be filled with None (and imputed by the pipeline).
    """
    model, feature_cols = _load_model_and_features()

    # Build a one-row DataFrame in the correct column order
    row = {col: state.get(col, None) for col in feature_cols}
    X = pd.DataFrame([row], columns=feature_cols)

    proba_home = model.predict_proba(X)[:, 1][0]  # probability home wins
    return float(proba_home)


if __name__ == "__main__":
    # Simple manual test using a fake state
    example_state = {
        "season": 2023,
        "week": 1,
        "quarter": 1,
        "seconds_remaining": 900 - 30,  # 30 seconds into Q1
        "score_diff_home": 0,
        "home_has_ball": 1,
        "yardline_100": 75,  # on opp 25
        "down": 1,
        "ydstogo": 10,
    }

    p = predict_home_win_prob(example_state)
    print("Example state home win probability:", p)
