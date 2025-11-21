"""
Compatibility wrapper so older code can still import:

    from backend.models.ingame_predict import predict_home_win_prob

We now delegate to the new winprob_model implementation.
"""

from typing import Any, Dict

from backend.models.winprob_model.predict import predict_home_win_prob as _predict


def predict_home_win_prob(state: Dict[str, Any]) -> float:
    """
    Forwarder to backend.models.winprob_model.predict.predict_home_win_prob
    so existing imports keep working.
    """
    return _predict(state)
