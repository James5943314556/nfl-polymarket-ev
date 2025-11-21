from dataclasses import asdict
from typing import Literal

from backend.markets.nfl_games import (
    load_game_markets,
    pick_full_game_moneyline,
)
from backend.models.ingame_predict import predict_home_win_prob
from backend.backtest.ev_utils import compute_ev_for_long, EVResult


StateSide = Literal["home_yes", "home_no"]


def compute_ev_for_game_state(
    slug: str,
    state: dict,
    side: StateSide,
    fee_cost: float = 0.01,
) -> EVResult:
    """
    Combine:
      - your trained in-game model (predict_home_win_prob)
      - Polymarket full-game moneyline for the given slug
      - EV math (including fees)

    Assumptions (good enough for now):
      - Event title is like "Bills vs. Texans"
      - YES = first team (Bills) = 'home'
      - NO  = second team (Texans) = 'away'
      - Model state is from the home team's perspective (p_home_win)
      - You are LONG either home_yes (YES side) or home_no (NO side)
    """
    # 1) Model probability from the current state
    p_home = predict_home_win_prob(state)

    # 2) Market prices from Polymarket
    game = load_game_markets(slug)
    ml = pick_full_game_moneyline(game)
    if ml is None:
        raise RuntimeError(f"No full-game moneyline market found for slug={slug}")

    # We interpret:
    #   YES price = home team price
    #   NO price  = away team price
    if side == "home_yes":
        market_price = ml.yes_price
        p_model = p_home
    elif side == "home_no":
        market_price = ml.no_price
        # Model probability for "NO" = away wins = 1 - p_home
        p_model = 1.0 - p_home
    else:
        raise ValueError(f"Unknown side: {side}")

    if market_price is None:
        raise RuntimeError(f"Market price is missing for side={side} in moneyline market {ml.market_id}")

    # 3) EV calculation (long that side)
    ev = compute_ev_for_long(
        p_model=p_model,
        market_price=market_price,
        fee_cost=fee_cost,
    )

    return ev


if __name__ == "__main__":
    # Example: Bills vs Texans, some fake state
    slug = "nfl-buf-hou-2025-11-20"

    # Example state: Q1, 10:00 left, Bills up 7–0, Bills ball at opp 35, 2nd & 6
    example_state = {
        "season": 2025,
        "week": 12,
        "quarter": 1,
        "seconds_remaining": 10 * 60,
        "score_diff_home": 7,  # Bills (home) +7
        "home_has_ball": 1,
        "yardline_100": 35,
        "down": 2,
        "ydstogo": 6,
    }

    print("Running example EV for home YES (Bills) ...")
    ev_home_yes = compute_ev_for_game_state(
        slug=slug,
        state=example_state,
        side="home_yes",
        fee_cost=0.01,  # 1 cent per contract fees
    )

    print("EV result (home YES):")
    print(asdict(ev_home_yes))
