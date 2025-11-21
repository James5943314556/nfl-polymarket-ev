import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class BinaryMarketSnapshot:
    market_id: str
    question: str
    yes_price: Optional[float]
    no_price: Optional[float]
    yes_token_id: Optional[str]
    no_token_id: Optional[str]


def parse_binary_market(m: Dict[str, Any]) -> BinaryMarketSnapshot:
    """
    Parse a Polymarket binary market object (as returned by Gamma)
    into a clean BinaryMarketSnapshot.

    Handles:
      - outcomes: '["Yes","No"]' or ["Yes","No"]
      - outcomePrices: '["0.461","0.539"]' or ["0.461","0.539"]
      - clobTokenIds: '["...","..."]' or ["...","..."]
    """

    def decode_list(raw) -> List[str]:
        if not raw:
            return []
        if isinstance(raw, str):
            try:
                return list(json.loads(raw))
            except json.JSONDecodeError:
                # fall back: treat whole string as one element
                return [raw]
        if isinstance(raw, list):
            return raw
        return [str(raw)]

    outcomes = decode_list(m.get("outcomes"))
    prices_raw = decode_list(m.get("outcomePrices"))
    tokens = decode_list(m.get("clobTokenIds"))

    # We assume standard YES/NO order, but stay defensive.
    yes_idx = 0
    no_idx = 1 if len(outcomes) > 1 else None

    def safe_float(x):
        try:
            return float(x)
        except Exception:
            return None

    yes_price = safe_float(prices_raw[yes_idx]) if len(prices_raw) > yes_idx else None
    no_price = safe_float(prices_raw[no_idx]) if no_idx is not None and len(prices_raw) > no_idx else None

    yes_token_id = tokens[yes_idx] if len(tokens) > yes_idx else None
    no_token_id = tokens[no_idx] if no_idx is not None and len(tokens) > no_idx else None

    return BinaryMarketSnapshot(
        market_id=str(m.get("id")),
        question=m.get("question") or "",
        yes_price=yes_price,
        no_price=no_price,
        yes_token_id=yes_token_id,
        no_token_id=no_token_id,
    )
