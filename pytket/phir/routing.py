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

def eo_sort_rounds(q1l, q2l) -> tuple[int, int]:
    '''Find the number of even and odd rounds to get from ordering state one to state two'''

    even_rounds = odd_rounds = 0
    #commented lines to remove q1l manipulation, uncomment for info about specific swaps
    # p = [q2l.index(q) for q in q1l]
    q2l_inv = inverse(q2l)
    p = [q2l_inv[q] for q in q1l]
    final_p = [i for i in range(len(p))]
    # while q1l != q2l:
    while p != final_p:
        e = o = 0
        # even cycle
        for i in range(0, len(q1l)-1, 2):
            if p[i] > p[i+1]:
                e = 1
                # q1l[i], q1l[i+1] = q1l[i+1], q1l[i]
                p[i], p[i+1] = p[i+1], p[i]
        # odd cycle
        for i in range(1, len(q1l)-1, 2):
            if p[i] > p[i+1]:
                o = 1
                # q1l[i], q1l[i+1] = q1l[i+1], q1l[i]
                p[i], p[i+1] = p[i+1], p[i]
        even_rounds += e
        odd_rounds += o

    return even_rounds, odd_rounds

def calc_cost(even_rounds, odd_rounds):
    '''Calculate the cost of routing from state one to state two '''
    
    #units in us
    combine = 130
    flip = 200
    split = 130
    shift_1_cw = 265
    rshift_1_cw = 265

    even_swap = combine + flip + split
    odd_swap = shift_1_cw + combine + flip + split + rshift_1_cw

    return (even_rounds * even_swap + odd_rounds * odd_swap)

