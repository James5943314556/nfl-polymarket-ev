from dataclasses import dataclass
from typing import List, Optional

from backend.markets.gamma_client import GammaClient
from backend.markets.price_utils import parse_binary_market, BinaryMarketSnapshot


@dataclass
class GameMarkets:
    slug: str
    event_id: str
    title: str
    markets: List[BinaryMarketSnapshot]


def load_game_markets(slug: str) -> GameMarkets:
    """
    Given a Polymarket game slug, fetch the event and parse
    all of its binary markets (Yes/No) into BinaryMarketSnapshot objects.
    """
    client = GammaClient()

    event = client.get_event_by_slug(slug)
    event_id = str(event.get("id"))
    title = (
        event.get("title")
        or event.get("name")
        or event.get("ticker")
        or slug
    )

    raw_markets = event.get("markets") or []

    snapshots: List[BinaryMarketSnapshot] = []
    for m in raw_markets:
        try:
            snap = parse_binary_market(m)
            snapshots.append(snap)
        except Exception as e:
            print(f"Skipping market {m.get('id')} due to parse error: {e}")

    return GameMarkets(
        slug=slug,
        event_id=event_id,
        title=title,
        markets=snapshots,
    )


def pick_full_game_moneyline(game: GameMarkets) -> Optional[BinaryMarketSnapshot]:
    """
    Heuristic to pick the *full-game* moneyline market for a game.

    What we saw for Bills vs Texans:

      - Game title: "Bills vs. Texans"
      - Full-game moneyline question: "Bills vs. Texans"
      - 1H moneyline question: "Bills vs. Texans: 1H Moneyline"
      - Totals/spreads have things like "O/U", "Spread", "Team Total" in the question.

    Strategy:
      1) Prefer markets whose question exactly equals game.title.
      2) If none, prefer questions that start with game.title AND
         do NOT contain keywords like "1H", "Team Total", "O/U", "Spread".
    """

    title = game.title or ""

    # 1) Exact title match
    exact_matches = [
        m for m in game.markets
        if m.question.strip() == title.strip()
    ]
    if exact_matches:
        # If multiple for some weird reason, just take the first
        return exact_matches[0]

    # 2) Fuzzy: starts with title, but avoid obvious non-full-game keywords
    bad_keywords = ["1h", "team total", "o/u", "spread", "total:"]
    candidates: List[BinaryMarketSnapshot] = []
    lowered_title = title.lower()

    for m in game.markets:
        q = (m.question or "").strip()
        q_lower = q.lower()

        if not q or not lowered_title:
            continue

        if not q_lower.startswith(lowered_title):
            continue

        if any(kw in q_lower for kw in bad_keywords):
            continue

        candidates.append(m)

    if candidates:
        return candidates[0]

    return None
