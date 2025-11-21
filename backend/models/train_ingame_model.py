import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score

STATE_PATH = "backend/data/state_dataset.parquet"
MODEL_PATH = "backend/models/ingame_model.pkl"


def load_state_data():
    if not os.path.exists(STATE_PATH):
        raise FileNotFoundError(f"State dataset not found at {STATE_PATH}")

    print(f"Loading state dataset from {STATE_PATH} ...")
    df = pd.read_parquet(STATE_PATH)
    print("Loaded state dataset. Shape:", df.shape)

    # Basic sanity filters
    df = df[df["seconds_remaining"].notna()]
    df = df[df["score_diff_home"].notna()]
    df = df[df["yardline_100"].notna()]
    df = df[df["down"].notna()]
    df = df[df["ydstogo"].notna()]
    df = df[df["quarter"].notna()]
    df = df[df["home_win"].notna()]

    print("After filters:", df.shape)

    return df


def build_features_and_target(df: pd.DataFrame):
    """
    Build X (features) and y (target) from the state dataset.
    We train from the home team's perspective: target is home_win (1 if home wins).
    """

    feature_cols = [
        "season",
        "week",
        "quarter",
        "seconds_remaining",
        "score_diff_home",
        "home_has_ball",
        "yardline_100",
        "down",
        "ydstogo",
        # "pregame_wp_home",  # we'll add this later once we have a pregame model
    ]

    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in state dataset: {missing}")

    X = df[feature_cols].copy()
    y = df["home_win"].astype(int)

    return X, y, feature_cols


def train_ingame_model():
    # --------------------------------------------
    # Load data
    # --------------------------------------------
    df = load_state_data()
    X, y, feature_cols = build_features_and_target(df)

    print("Feature columns:", feature_cols)
    print("X shape:", X.shape, "y shape:", y.shape)

    # --------------------------------------------
    # Train / test split
    # --------------------------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # --------------------------------------------
    # Build pipeline: Imputer + Scaler + Logistic Regression
    # --------------------------------------------
    model = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    max_iter=1000,
                    solver="lbfgs",
                ),
            ),
        ]
    )

    print("Training in-game win probability model (logistic regression)...")
    model.fit(X_train, y_train)
    print("Training complete.")

    # --------------------------------------------
    # Evaluate on test set
    # --------------------------------------------
    y_proba = model.predict_proba(X_test)[:, 1]  # probability home wins
    brier = brier_score_loss(y_test, y_proba)
    auc = roc_auc_score(y_test, y_proba)

    print(f"Test Brier score (lower is better): {brier:.4f}")
    print(f"Test ROC AUC (higher is better):   {auc:.4f}")

    # --------------------------------------------
    # Save model
    # --------------------------------------------
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_cols": feature_cols,
        },
        MODEL_PATH,
    )

    print(f"Saved in-game model to {MODEL_PATH}")


if __name__ == "__main__":
    train_ingame_model()
