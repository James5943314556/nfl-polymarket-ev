import joblib
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    brier_score_loss,
    log_loss,
)
from sklearn.model_selection import train_test_split

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
THIS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = THIS_DIR.parent.parent  # .../backend
DATA_PATH = BACKEND_DIR / "data" / "state_dataset.parquet"
MODEL_PATH = THIS_DIR / "model.pkl"

FEATURE_COLS = [
    "quarter",
    "seconds_remaining",
    "score_diff_home",
    "home_has_ball",
    "yardline_100",
    "down",
    "ydstogo",
]


# --------------------------------------------------------------------
# Data loading
# --------------------------------------------------------------------
def load_data() -> Tuple[np.ndarray, np.ndarray]:
    print(f"Loading data from {DATA_PATH} ...")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"State dataset not found at {DATA_PATH}")

    df = pd.read_parquet(DATA_PATH)

    # Basic sanity checks
    missing_cols = [c for c in FEATURE_COLS + ["home_win"] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing columns: {missing_cols}")

    # Minimal cleaning
    df = df.dropna(subset=["home_win"])
    df["home_win"] = df["home_win"].astype(int)

    # Fill NaNs in features conservatively
    for col in FEATURE_COLS:
        if df[col].isna().any():
            if df[col].dtype.kind in "ifu":
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(0)

    X = df[FEATURE_COLS].astype(float).to_numpy()
    y = df["home_win"].to_numpy()

    print(f"Dataset shape: X={X.shape}, y={y.shape}")
    return X, y


# --------------------------------------------------------------------
# Metrics helper
# --------------------------------------------------------------------
def compute_metrics(y_true: np.ndarray, prob: np.ndarray) -> Dict[str, float]:
    prob = np.clip(prob, 1e-6, 1 - 1e-6)
    auc = roc_auc_score(y_true, prob)
    brier = brier_score_loss(y_true, prob)
    ll = log_loss(y_true, prob)
    return {"auc": auc, "brier": brier, "log_loss": ll}


# --------------------------------------------------------------------
# Training / calibration
# --------------------------------------------------------------------
def train() -> None:
    X, y = load_data()

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # Base model: logistic regression (conservative, interpretable)
    base_model = LogisticRegression(max_iter=1000)
    print("Fitting logistic regression...")
    base_model.fit(X_train, y_train)

    # Raw probabilities on validation set
    val_raw = base_model.predict_proba(X_val)[:, 1]

    # --- candidate 1: raw (no calibration) ---
    metrics_raw = compute_metrics(y_val, val_raw)
    print("\n=== Raw model (no calibration) ===")
    print(f"AUC:        {metrics_raw['auc']:.4f}")
    print(f"Brier:      {metrics_raw['brier']:.4f}")
    print(f"Log loss:   {metrics_raw['log_loss']:.4f}")

    # --- candidate 2: isotonic regression ---
    print("\nFitting isotonic regression calibrator...")
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(val_raw, y_val)
    val_iso = iso.predict(val_raw)
    metrics_iso = compute_metrics(y_val, val_iso)
    print("\n=== Isotonic-calibrated model ===")
    print(f"AUC:        {metrics_iso['auc']:.4f}")
    print(f"Brier:      {metrics_iso['brier']:.4f}")
    print(f"Log loss:   {metrics_iso['log_loss']:.4f}")

    # --- candidate 3: Platt scaling (logistic on raw prob) ---
    print("\nFitting Platt (sigmoid) calibrator...")
    platt = LogisticRegression(max_iter=1000)
    platt.fit(val_raw.reshape(-1, 1), y_val)
    val_platt = platt.predict_proba(val_raw.reshape(-1, 1))[:, 1]
    metrics_platt = compute_metrics(y_val, val_platt)
    print("\n=== Platt-calibrated model ===")
    print(f"AUC:        {metrics_platt['auc']:.4f}")
    print(f"Brier:      {metrics_platt['brier']:.4f}")
    print(f"Log loss:   {metrics_platt['log_loss']:.4f}")

    # ----------------------------------------------------------------
    # Pick the best calibration by Brier score (calibration-focused)
    # ----------------------------------------------------------------
    candidates = {
        "none": {"metrics": metrics_raw, "calibrator": None},
        "isotonic": {"metrics": metrics_iso, "calibrator": iso},
        "platt": {"metrics": metrics_platt, "calibrator": platt},
    }

    best_type = min(candidates.keys(), key=lambda k: candidates[k]["metrics"]["brier"])
    best_cal = candidates[best_type]["calibrator"]
    best_metrics = candidates[best_type]["metrics"]

    print("\n=== Chosen calibration ===")
    print(f"Type:   {best_type}")
    print(f"Brier:  {best_metrics['brier']:.4f}")
    print(f"AUC:    {best_metrics['auc']:.4f}")
    print(f"LogLoss:{best_metrics['log_loss']:.4f}")

    artifacts: Dict[str, Any] = {
        "base_model": base_model,
        "calibrator_type": best_type,
        "calibrator": best_cal,
        "feature_cols": FEATURE_COLS,
        "metrics": {
            "raw": metrics_raw,
            "isotonic": metrics_iso,
            "platt": metrics_platt,
            "chosen": best_type,
        },
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, MODEL_PATH)
    print(f"\nSaved model + calibrator to {MODEL_PATH}")


if __name__ == "__main__":
    train()
