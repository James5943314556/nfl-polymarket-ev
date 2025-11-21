import joblib
import numpy as np
from pathlib import Path

ARTIFACTS = None
ARTIFACTS_PATH = Path(__file__).resolve().parent / "model.pkl"


def _load_artifacts():
    global ARTIFACTS
    if ARTIFACTS is None:
        ARTIFACTS = joblib.load(ARTIFACTS_PATH)
    return ARTIFACTS


def predict_home_win_prob(state: dict) -> float:
    """
    state = {
        'quarter': int,
        'seconds_remaining': int,
        'score_diff_home': int,
        'home_has_ball': int,
        'yardline_100': int,
        'down': int,
        'ydstogo': int
    }
    """

    artifacts = _load_artifacts()

    # extract objects
    feature_cols = artifacts["feature_cols"]
    base_model = artifacts["base_model"]
    calibrator = artifacts["calibrator"]

    # Build input row
    X = np.array([[state[c] for c in feature_cols]], dtype=float)

    # Predict raw probabilities from logistic regression
    raw_proba = base_model.predict_proba(X)[0, 1]

    # Apply calibrator if present
    if calibrator is not None:
        calibrated = calibrator.predict(np.array([raw_proba]))[0]
        return float(calibrated)

    # otherwise return raw
    return float(raw_proba)
