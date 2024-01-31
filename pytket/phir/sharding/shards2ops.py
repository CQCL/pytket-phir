##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from typing import TYPE_CHECKING, TypeAlias

if TYPE_CHECKING:
    from pytket.unit_id import UnitID

    from .shard import Shard, ShardLayer

Layer: TypeAlias = list[list[int]]


def parse_shards_naive(
    shards: set["Shard"],
) -> tuple[list[Layer], list["ShardLayer"]]:
    """Parse a set of shards and return a circuit representation for placement."""
    layers: list[Layer] = []
    shards_in_layer: list[ShardLayer] = []
    scheduled: set[int] = set()
    num_shards: int = len(shards)
    qubit_id: int = 0
    qubits2ids: dict["UnitID", int] = {}

    while len(scheduled) < num_shards:
        layer: Layer = []

        # Iterate the shards, looking for shards whose dependencies have been
        # satisfied, or initially, shards with no dependencies
        to_schedule: ShardLayer = [
            s for s in shards if s.depends_upon.issubset(scheduled)
        ]
        shards_in_layer.append(to_schedule)
        shards.difference_update(to_schedule)

        for shard in to_schedule:
            op: list[int] = []
            # if there are more than 2 qubits used, treat them all as parallel sq ops
            # one qubit will just be a single sq op
            # 3 or more will be 3 or more parallel sq ops
            # when iterating through qubits,
            # map all the qubits to a unique id to prevent duplicates in placement
            if len(shard.qubits_used) != 2:  # noqa: PLR2004
                for qubit in shard.qubits_used:
                    qid, qubits2ids, qubit_id = assign_qubit_id(
                        qubit, qubits2ids, qubit_id
                    )
                    op = [qid]
                    layer.append(op)
            else:
                for qubit in shard.qubits_used:
                    qid, qubits2ids, qubit_id = assign_qubit_id(
                        qubit, qubits2ids, qubit_id
                    )
                    op.append(qid)
                layer.append(op)

            scheduled.add(shard.ID)

        layers.append(layer)

    return layers, shards_in_layer


def assign_qubit_id(
    qubit: "UnitID", qubits2ids: dict["UnitID", int], qubit_id: int
) -> tuple[int, dict["UnitID", int], int]:
    """A helper function for managing qubit ids."""
    if qubit not in qubits2ids:
        qubits2ids[qubit] = qubit_id
        qubit_id += 1
    qid = qubits2ids[qubit]
    return qid, qubits2ids, qubit_id
