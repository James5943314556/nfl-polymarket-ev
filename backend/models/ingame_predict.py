"""
Compatibility shim.

The real implementation lives in backend.models.winprob_model.predict,
but older code still imports from backend.models.ingame_predict.
"""

from backend.models.winprob_model.predict import (
    predict_winprob,
    predict_home_win_prob,
)

__all__ = ["predict_winprob", "predict_home_win_prob"]
