##############################################################################
#
# Copyright (c) 2026 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# ruff: file-ignore[implicit-namespace-package, print]

"""Benchmark the optimized placement hot path on a synthetic full layer."""

from timeit import repeat

from pytket.phir.placement import optimized_place

NUM_QUBITS = 256
ITERATIONS = 1_000
REPEATS = 5

# 64 non-overlapping TQ ops and 64 non-overlapping SQ ops.
OPS = [[i, NUM_QUBITS - 1 - i] for i in range(0, 128, 2)] + [
    [i] for i in range(128, NUM_QUBITS, 2)
]
TQ_OPTIONS = set(range(0, 128, 2))
SQ_OPTIONS = set(range(NUM_QUBITS))
PREV_STATE = list(reversed(range(NUM_QUBITS)))


def main() -> None:
    """Run the placement benchmark and print the best timing."""
    elapsed = min(
        repeat(
            lambda: optimized_place(
                OPS, TQ_OPTIONS, SQ_OPTIONS, NUM_QUBITS, PREV_STATE
            ),
            number=ITERATIONS,
            repeat=REPEATS,
        )
    )
    print(
        f"input: qubits={NUM_QUBITS}, tq_ops=64, sq_ops=64, "
        f"iterations={ITERATIONS}, repeats={REPEATS}"
    )
    print(f"best_seconds={elapsed:.6f}")
    print(f"microseconds_per_call={elapsed / ITERATIONS * 1_000_000:.2f}")


if __name__ == "__main__":
    main()
