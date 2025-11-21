# backend/api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal

from backend.backtest.game_ev import compute_ev_for_game_state
from backend.backtest.ev_utils import EVResult


app = FastAPI()

# Allow local Next.js dev to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can tighten this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------
# Request / Response models
# -------------------------------

class GameState(BaseModel):
    # You can add season/week later if you want
    quarter: int = Field(..., ge=1, le=5)
    seconds_remaining: int = Field(..., ge=0)
    score_diff_home: int  # home_score - away_score
    home_has_ball: bool
    yardline_100: int = Field(..., ge=0, le=100)
    down: int = Field(..., ge=1, le=4)
    ydstogo: int = Field(..., ge=1)


class EVRequest(BaseModel):
    slug: str  # e.g. "nfl-buf-hou-2025-11-20"
    side: Literal["home_yes", "home_no"]
    state: GameState
    fee_cost: float = 0.01  # in price-space, e.g. 0.01 = 1 cent


class EVResponse(BaseModel):
    p_model: float
    fair_price: float
    market_price: float
    fee_cost: float
    edge_raw: float
    edge_after_fees: float
    ev_per_contract: float


# -------------------------------
# Endpoint
# -------------------------------

@app.post("/ev/game", response_model=EVResponse)
def ev_for_game(request: EVRequest):
    """
    Compute EV for a given Polymarket NFL game slug + live game state.

    Assumptions:
      - Slug corresponds to a valid NFL game on Polymarket (Bills vs Texans etc.)
      - YES = home team, NO = away team, from the model's perspective
      - The model is trained on home_win (so home_yes uses p_home,
        home_no uses 1 - p_home).
    """

    # Build the state dict expected by compute_ev_for_game_state
    state_dict = {
        # You can add season/week here later if you want
        "season": 2025,
        "week": 1,
        "quarter": request.state.quarter,
        "seconds_remaining": request.state.seconds_remaining,
        "score_diff_home": request.state.score_diff_home,
        "home_has_ball": 1 if request.state.home_has_ball else 0,
        "yardline_100": request.state.yardline_100,
        "down": request.state.down,
        "ydstogo": request.state.ydstogo,
    }

    try:
        ev: EVResult = compute_ev_for_game_state(
            slug=request.slug,
            state=state_dict,
            side=request.side,
            fee_cost=request.fee_cost,
        )
    except Exception as e:
        # Surface a clean error to the frontend
        raise HTTPException(status_code=400, detail=str(e))

    return EVResponse(
        p_model=ev.p_model,
        fair_price=ev.fair_price,
        market_price=ev.market_price,
        fee_cost=ev.fee_cost,
        edge_raw=ev.edge_raw,
        edge_after_fees=ev.edge_after_fees,
        ev_per_contract=ev.ev_per_contract,
    )
