import nfl_data_py as nfl
import pandas as pd
import os

# ---------------------------------------------
# CONFIG
# ---------------------------------------------
SEASONS = list(range(2015, 2024))  # free, modern NFL dataset
OUTPUT_PATH = "backend/data/pbp.parquet"


def fetch_pbp():
    print(f"Fetching play-by-play for seasons: {SEASONS}")

    # ---------------------------------------------
    # Download play-by-play
    # ---------------------------------------------
    pbp = nfl.import_pbp_data(
        years=SEASONS,
        downcast=True,
        cache=False
    )

    print("Downloaded. Shape:", pbp.shape)

    # ---------------------------------------------
    # Select columns (some may not exist)
    # ---------------------------------------------
    desired_cols = [
        "game_id",
        "season",
        "week",
        "home_team",
        "away_team",
        "qtr",                      # quarter
        "game_seconds_remaining",
        "half_seconds_remaining",
        "score_differential",
        "posteam",
        "defteam",
        "yardline_100",
        "down",
        "ydstogo",
        "play_type",
        "drive",
        "drive_result",            # may be missing
        "td_team",
        "posteam_score",
        "defteam_score",
        "total_home_score",
        "total_away_score",
        "play_id",
        "epa",
    ]

    available_cols = [c for c in desired_cols if c in pbp.columns]
    missing_cols = sorted(set(desired_cols) - set(available_cols))

    if missing_cols:
        print("Warning: missing columns:", missing_cols)

    pbp = pbp[available_cols]

    # ---------------------------------------------
    # Rename qtr → quarter if present
    # ---------------------------------------------
    if "qtr" in pbp.columns:
        pbp = pbp.rename(columns={"qtr": "quarter"})

    # ---------------------------------------------
    # Save the cleaned dataset
    # ---------------------------------------------
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    pbp.to_parquet(OUTPUT_PATH, index=False)

    print(f"Saved cleaned PBP to {OUTPUT_PATH}")
    print("Done.")


if __name__ == "__main__":
    fetch_pbp()
