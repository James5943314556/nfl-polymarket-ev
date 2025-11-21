from backend.markets.gamma_client import GammaClient
from backend.markets.config import NFL_TAG_ID
from backend.markets.price_utils import parse_binary_market


def main():
    client = GammaClient()

    print(f"NFL_TAG_ID = {NFL_TAG_ID}")

    # 1) Get some NFL markets under tag 450
    markets = client.get_markets(
        active=True,
        closed=False,
        limit=20,
        tag_id=NFL_TAG_ID,
    )
    print(f"Total active NFL-tagged markets (limit 20): {len(markets)}")

    if not markets:
        print("No markets found for NFL tag; nothing to inspect.")
        return

    # 2) Parse and print first few as binary snapshots
    print("\n=== Parsed binary snapshots (first 10) ===")
    for m in markets[:10]:
        snap = parse_binary_market(m)
        print("\n-------------------------------------")
        print(f"Market ID:   {snap.market_id}")
        print(f"Question:    {snap.question}")
        print(f"YES price:   {snap.yes_price} (token {snap.yes_token_id})")
        print(f"NO  price:   {snap.no_price} (token {snap.no_token_id})")


if __name__ == "__main__":
    main()
