import os
import pandas as pd

from backend.models.ingame_predict import predict_home_win_prob
from backend.backtest.ev_utils import compute_ev


STATE_PATH = "backend/data/state_dataset.parquet"


def load_sample_state():
    if not os.path.exists(STATE_PATH):
        raise FileNotFoundError(f"State dataset not found at {STATE_PATH}")

    print(f"Loading state dataset from {STATE_PATH} ...")
    df = pd.read_parquet(STATE_PATH)
    print("Full state dataset shape:", df.shape)

    # Simple filter to avoid weird late-game states:
    # use only Q1–Q3 and non-extreme scores for now
    df = df[df["quarter"].between(1, 3)]
    df = df[df["seconds_remaining"] > 0]

    # Take one random row as an example
    sample = df.sample(1, random_state=42).iloc[0]

    print("Sample row:")
    print(sample[[
        "season", "week", "home_team", "away_team",
        "quarter", "seconds_remaining",
        "home_score", "away_score",
        "score_diff_home", "home_has_ball",
        "yardline_100", "down", "ydstogo",
        "home_win",
    ]])

    # Build the state dict expected by predict_home_win_prob
    state = {
        "season": int(sample["season"]),
        "week": int(sample["week"]),
        "quarter": int(sample["quarter"]),
        "seconds_remaining": float(sample["seconds_remaining"]),
        "score_diff_home": float(sample["score_diff_home"]),
        "home_has_ball": int(sample["home_has_ball"]),
        "yardline_100": float(sample["yardline_100"]),
        "down": int(sample["down"]),
        "ydstogo": float(sample["ydstogo"]),
    }

    # Also return whether the home team actually won (for sanity)
    home_win_actual = int(sample["home_win"])

    return state, home_win_actual


def main():
    # 1) Load a real state from the dataset
    state, home_win_actual = load_sample_state()

    print("\nState dict passed to model:")
    for k, v in state.items():
        print(f"  {k}: {v}")

    # 2) Get model probability
    p_home = predict_home_win_prob(state)
    print(f"\nModel home win probability: {p_home:.4f}")

    # 3) Assume a fake market price and fee for demonstration
    market_price = 0.55   # fake Polymarket YES price
    fee_cost = 0.01       # assume 1 cent friction per contract

    ev_result = compute_ev(p_home, market_price, fee_cost)

    print("\nEV breakdown (assuming market price = 0.55, fee = 0.01):")
    print(f"  Model p_home:        {ev_result.p_model:.4f}")
    print(f"  Fair price:          {ev_result.fair_price:.4f}")
    print(f"  Market price:        {ev_result.market_price:.4f}")
    print(f"  Raw edge:            {ev_result.edge_raw:.4f}")
    print(f"  Edge after fees:     {ev_result.edge_after_fees:.4f}")
    print(f"  EV per contract:     {ev_result.ev_per_contract:.4f}")

    print(f"\nDid home actually win this game? {home_win_actual} (1=yes, 0=no)")


if __name__ == "__main__":
    main()
