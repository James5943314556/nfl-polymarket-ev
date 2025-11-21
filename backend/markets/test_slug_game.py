from backend.markets.nfl_games import load_game_markets, pick_full_game_moneyline


def main():
    slug = input("Enter Polymarket game slug (after /event/): ").strip()

    game = load_game_markets(slug)

    print("\n=== Game info ===")
    print(f"Slug:      {game.slug}")
    print(f"Event ID:  {game.event_id}")
    print(f"Title:     {game.title}")
    print(f"# markets: {len(game.markets)}")

    ml = pick_full_game_moneyline(game)

    if ml is None:
        print("\nNo full-game moneyline market found by heuristic.")
        return

    print("\n=== Picked full-game moneyline market ===")
    print(f"Market ID:   {ml.market_id}")
    print(f"Question:    {ml.question}")
    print(f"YES price:   {ml.yes_price} (token {ml.yes_token_id})")
    print(f"NO  price:   {ml.no_price} (token {ml.no_token_id})")


if __name__ == "__main__":
    main()
