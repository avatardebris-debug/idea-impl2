#!/usr/bin/env python3
"""Demo: create players, query attributes, and run a match."""

from player_attribute_library import (
    PlayerAttribute,
    create_player,
    get_attribute,
    get_all_attributes,
    match_players,
)

__all__ = ["main"]


def main():
    # 1. Create player records
    print("=" * 60)
    print("  PLAYER ATTRIBUTE LIBRARY — DEMO")
    print("=" * 60)

    messi = create_player(
        "Messi",
        speed=85,
        shooting=95,
        passing=92,
        defending=35,
        physical=65,
        mental=90,
    )
    ronaldo = create_player(
        "Ronaldo",
        speed=88,
        shooting=96,
        passing=80,
        defending=35,
        physical=80,
        mental=88,
    )
    neymar = create_player(
        "Neymar",
        speed=90,
        shooting=88,
        passing=85,
        defending=30,
        physical=55,
        mental=82,
    )
    kante = create_player(
        "Kante",
        speed=75,
        shooting=50,
        passing=72,
        defending=88,
        physical=85,
        mental=86,
    )

    players = [messi, ronaldo, neymar, kante]

    # 2. Display all attributes
    print("\n--- All Player Attributes ---")
    for p in players:
        attrs = get_all_attributes(p)
        print(f"\n  {p.name}:")
        for attr, val in attrs.items():
            print(f"    {attr:>10}: {val:5.1f}")

    # 3. Query individual attributes
    print("\n--- Individual Attribute Lookup ---")
    print(f"  Messi shooting : {get_attribute(messi, 'shooting')}")
    print(f"  Kante defending: {get_attribute(kante, 'defending')}")
    print(f"  Neymar speed   : {get_attribute(neymar, 'speed')}")

    # 4. Validate clamping
    print("\n--- Validation (clamping to 0–100) ---")
    over = create_player("Over", speed=150, shooting=-10)
    print(f"  'Over' speed (clamped from 150): {get_attribute(over, 'speed')}")
    print(f"  'Over' shooting (clamped from -10): {get_attribute(over, 'shooting')}")

    # 5. Match players against a target profile
    print("\n--- Match Players (target = Messi) ---")
    target = messi  # use Messi as the target profile
    results = match_players(target, players, metric="cosine", top_n=4)
    print(f"\n  Target: {target.name}")
    print(f"  Metric: cosine similarity")
    print(f"  {'Rank':<6} {'Player':<12} {'Score':>8}")
    print(f"  {'-'*6} {'-'*12} {'-'*8}")
    for i, r in enumerate(results, 1):
        print(f"  {i:<6} {r['player'].name:<12} {r['score']:>8.4f}")

    # 6. Euclidean distance match
    print("\n--- Match Players (target = Messi, euclidean) ---")
    results_euc = match_players(target, players, metric="euclidean", top_n=4)
    print(f"\n  Target: {target.name}")
    print(f"  Metric: euclidean (inverted)")
    print(f"  {'Rank':<6} {'Player':<12} {'Score':>8}")
    print(f"  {'-'*6} {'-'*12} {'-'*8}")
    for i, r in enumerate(results_euc, 1):
        print(f"  {i:<6} {r['player'].name:<12} {r['score']:>8.4f}")

    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
