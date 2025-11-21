import joblib
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    brier_score_loss,
    roc_auc_score,
    log_loss,
)

# Paths
MODEL_PATH = Path("backend/models/ingame_model.pkl")
STATE_DATASET_PATH = Path("backend/data/state_dataset.parquet")

# Features we currently train on
FEATURE_COLS = [
    "quarter",
    "seconds_remaining",
    "score_diff_home",
    "home_has_ball",
    "yardline_100",
    "down",
    "ydstogo",
]

TARGET_COL = "home_win"


def main():
    print(f"Loading state dataset from {STATE_DATASET_PATH} ...")
    df = pd.read_parquet(STATE_DATASET_PATH)
    print(f"Full dataset shape: {df.shape}")

    # Make sure target exists and is numeric
    if TARGET_COL not in df.columns:
        raise ValueError(f"Target column '{TARGET_COL}' not found in dataset.")

    # Basic sanity on seasons
    if "season" not in df.columns:
        raise ValueError("Column 'season' not found in dataset.")

    seasons = sorted(df["season"].unique())
    if len(seasons) < 2:
        raise ValueError(
            f"Need at least 2 seasons for train/eval split, found {seasons}"
        )

    eval_season = seasons[-1]
    print(f"Using season {eval_season} as evaluation holdout")

    df_eval = df[df["season"] == eval_season].copy()
    print(f"Eval subset shape: {df_eval.shape}")

    # Ensure all feature cols exist
    missing = [c for c in FEATURE_COLS if c not in df_eval.columns]
    if missing:
        raise ValueError(f"Missing feature columns in eval set: {missing}")

    X_eval = df_eval[FEATURE_COLS]
    y_eval = df_eval[TARGET_COL].astype(int)

    print(f"Loading model from {MODEL_PATH} ...")
    model = joblib.load(MODEL_PATH)
    print("Model loaded.")

    # Predict probabilities for home_win = 1
    p_eval = model.predict_proba(X_eval)[:, 1]

    # Metrics
    brier = brier_score_loss(y_eval, p_eval)
    auc = roc_auc_score(y_eval, p_eval)
    ll = log_loss(y_eval, p_eval)

    print("\n=== Evaluation on holdout season ===")
    print(f"Season:           {eval_season}")
    print(f"Num samples:      {len(df_eval)}")
    print(f"Brier score:      {brier:.4f}  (lower is better, 0 is perfect)")
    print(f"ROC AUC:          {auc:.4f}  (0.5 ~ random, 1.0 perfect)")
    print(f"Log loss:         {ll:.4f}  (lower is better)")

    # Calibration by decile
    df_eval = df_eval.assign(p_model=p_eval)
    df_eval["bucket"] = (df_eval["p_model"] * 10).astype(int).clip(0, 9)

    bucket_stats = (
        df_eval.groupby("bucket")
        .agg(
            avg_p=("p_model", "mean"),
            empirical_win=(TARGET_COL, "mean"),
            count=(TARGET_COL, "size"),
        )
        .reset_index()
        .sort_values("bucket")
    )

    print("\n=== Calibration by decile bucket ===")
    print("bucket | count | avg_p | empirical_win")
    for _, row in bucket_stats.iterrows():
        print(
            f"{int(row['bucket']):>6} | "
            f"{int(row['count']):>5} | "
            f"{row['avg_p']:.3f} | "
            f"{row['empirical_win']:.3f}"
        )


if __name__ == "__main__":
    main()
