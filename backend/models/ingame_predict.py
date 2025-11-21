"""
Compatibility wrapper so existing code can still do:

    from backend.models.ingame_predict import predict_home_win_prob

and get the new win-probability model under the hood.
"""

from typing import Any, Dict

from backend.models.winprob_model.predict import predict_home_win_prob as _predict


def predict_home_win_prob(state: Dict[str, Any]) -> float:
    """
    Forward to backend.models.winprob_model.predict.predict_home_win_prob.
    """
    return _predict(state)
