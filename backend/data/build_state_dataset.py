import os
import pandas as pd

PBP_PATH = "backend/data/pbp.parquet"
OUTPUT_PATH = "backend/data/state_dataset.parquet"


def build_state_dataset():
    if not os.path.exists(PBP_PATH):
        raise FileNotFoundError(f"Play-by-play file not found at {PBP_PATH}")

    print(f"Loading PBP from {PBP_PATH} ...")
    pbp = pd.read_parquet(PBP_PATH)
    print("Loaded PBP. Shape:", pbp.shape)

    # --------------------------------------------------
    # Basic cleaning: keep only plays with an offense
    # --------------------------------------------------
    pbp = pbp[pbp["posteam"].notna()]
    pbp = pbp[pbp["yardline_100"].notna()]
    pbp = pbp[pbp["down"].notna()]
    pbp = pbp[pbp["ydstogo"].notna()]
    pbp = pbp[pbp["quarter"].notna()]

    print("After basic filters:", pbp.shape)

    # --------------------------------------------------
    # Final game result per game_id (target)
    # --------------------------------------------------
    # Take the last row per game_id to get final scores
    final_scores = (
        pbp.sort_values(["game_id", "quarter", "game_seconds_remaining"])
        .groupby("game_id")
        .tail(1)[["game_id", "total_home_score", "total_away_score"]]
        .rename(
            columns={
                "total_home_score": "final_home_score",
                "total_away_score": "final_away_score",
            }
        )
    )

    # Drop duplicates just in case
    final_scores = final_scores.drop_duplicates(subset=["game_id"])

    # Merge back onto pbp
    pbp = pbp.merge(final_scores, on="game_id", how="left")

    # Home team win target: 1 if home wins, else 0
    pbp["home_win"] = (pbp["final_home_score"] > pbp["final_away_score"]).astype(int)

    # --------------------------------------------------
    # Build state features from the home-team perspective
    # --------------------------------------------------
    # Current score
    pbp["home_score"] = pbp["total_home_score"]
    pbp["away_score"] = pbp["total_away_score"]
    pbp["score_diff_home"] = pbp["home_score"] - pbp["away_score"]

    # Possession: is the home team on offense?
    pbp["home_has_ball"] = (pbp["posteam"] == pbp["home_team"]).astype(int)

    # Simpler time feature
    pbp["seconds_remaining"] = pbp["game_seconds_remaining"]

    # Placeholder for pregame win probability (to be filled later)
    pbp["pregame_wp_home"] = pd.NA

    # --------------------------------------------------
    # Select columns for the state dataset
    # --------------------------------------------------
    state_cols = [
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "quarter",
        "seconds_remaining",
        "home_score",
        "away_score",
        "score_diff_home",
        "home_has_ball",
        "yardline_100",
        "down",
        "ydstogo",
        "play_type",
        "pregame_wp_home",
        "home_win",
    ]

    available_cols = [c for c in state_cols if c in pbp.columns]
    missing = sorted(set(state_cols) - set(available_cols))
    if missing:
        print("Warning: missing state columns:", missing)

    state_df = pbp[available_cols].copy()

    print("State dataset shape:", state_df.shape)

    # --------------------------------------------------
    # Save to parquet
    # --------------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    state_df.to_parquet(OUTPUT_PATH, index=False)
    print(f"Saved state dataset to {OUTPUT_PATH}")
    print("Done.")


if __name__ == "__main__":
    build_state_dataset()
