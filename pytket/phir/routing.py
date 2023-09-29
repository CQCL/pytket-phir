from __future__ import annotations

class TransportError(Exception):
    def __init__(self, a: list[int], b: list[int]):
        super().__init__(f"Traps different sizes: {len(a)} vs. {len(b)}")

class PermutationError(Exception):
    def __init__(self, lst: list[int]):
        super().__init__(f"List {lst} is not a permutation of range({len(lst)})")

def inverse(lst: list[int]) -> list[int]:
    '''Inverse of a permutation list. If a[i] = x, then inverse(a)[x] = i'''
    
    inv = [-1] * len(lst)
   
    for i, elem in enumerate(lst):
        if not 0 <= elem < len(lst) or inv[elem] != -1:
            raise PermutationError(lst)
        inv[elem] = i
    
    return inv

def transport_cost(init: list[int], goal: list[int], swap_cost: float) -> float:
    '''Cost of transport from init to goal.
    This is based on the number of parallel swaps performed by Odd-Even
    Transposition Sort, which is the maximum distance that any qubit travels.'''

    if len(init) != len(goal):
        raise TransportError(init, goal)
    
    n_swaps = max(abs(g-i) for i, g in zip(inverse(init), inverse(goal)))

    return n_swaps * swap_cost