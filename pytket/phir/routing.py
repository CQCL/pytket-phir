# Copyright (c) 2023 Quantinuum LLC.
# INSERT LICENSE HERE
"""
Routing functions. For simulation we don't need to create a sequence of
transport operations; we are only interested in the time cost to transport from
one state to another.
"""

from __future__ import annotations


def inverse(lst: list[int]) -> list[int]:
    """Inverse of a permutation list. If a[i] = x, then inverse(a)[x] = i."""
    inv = [-1] * len(lst)
    for (i, elem) in enumerate(lst):
        if not 0 <= elem < len(lst):
            raise ValueError(f"List contains element not in range: {elem}")
        if inv[elem] != -1:
            raise ValueError(f"List contains duplicate elements: {lst}")
        inv[elem] = i
    return inv

def transport_cost(init: list[int], goal: list[int], swap_cost: float) -> float:
    """Cost of transport from init to goal.

    This is based on the number of parallel swaps performed by Odd-Even
    Transposition Sort, which is the maximum distance that any qubit travels.
    """
    if len(init) != len(goal):
        raise ValueError(
            f"init and goal lists have different lengths: {len(init)} vs. {len(goal)}"
        )
    n_swaps = max(abs(g - i) for (i, g) in zip(inverse(init), inverse(goal)))
    return n_swaps * swap_cost
