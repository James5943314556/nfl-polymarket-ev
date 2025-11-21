from dataclasses import dataclass


@dataclass
class EVResult:
    """
    Expected value of going LONG one side of a binary contract.

    All prices are in [0, 1] (i.e., "cents" divided by 1.00).
    """
    p_model: float          # model-implied probability of this side winning
    fair_price: float       # p_model (since payoff is 1 if win, 0 if lose)
    market_price: float     # current price you're paying
    fee_cost: float         # effective fee per contract (in price-space, e.g. 0.01 = 1 cent)
    edge_raw: float         # fair_price - market_price
    edge_after_fees: float  # edge_raw - fee_cost
    ev_per_contract: float  # expected profit per contract after fees


def compute_ev_for_long(
    p_model: float,
    market_price: float,
    fee_cost: float = 0.01,
) -> EVResult:
    """
    Compute EV of going LONG one side of a binary (YES/NO) market.

    - p_model: your model's probability for this side (0–1)
    - market_price: current price for this side (0–1)
    - fee_cost: effective fees per contract in the same units

    If payoff is 1 on win and 0 on loss, the fair price is just p_model.
    """
    fair_price = p_model
    edge_raw = fair_price - market_price
    edge_after_fees = edge_raw - fee_cost
    ev_per_contract = edge_after_fees

    return EVResult(
        p_model=p_model,
        fair_price=fair_price,
        market_price=market_price,
        fee_cost=fee_cost,
        edge_raw=edge_raw,
        edge_after_fees=edge_after_fees,
        ev_per_contract=ev_per_contract,
    )


if __name__ == "__main__":
    # quick sanity check
    test = compute_ev_for_long(
        p_model=0.62,
        market_price=0.54,
        fee_cost=0.01,
    )
    print(test)
