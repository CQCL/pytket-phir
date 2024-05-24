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
    qid_count: int = 0
    qubits2ids: dict[UnitID, int] = {}

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
                    qid, qid_count = get_qid(qubit, qubits2ids, qid_count)
                    op = [qid]
                    layer.append(op)
            else:
                for qubit in shard.qubits_used:
                    qid, qid_count = get_qid(qubit, qubits2ids, qid_count)
                    op.append(qid)
                layer.append(op)

            scheduled.add(shard.ID)

        layers.append(layer)

    return layers, shards_in_layer


def get_qid(
    qubit: "UnitID", qubits2ids: dict["UnitID", int], qid_count: int
) -> tuple[int, int]:
    """Get qubit ID even if it is missing in the dict."""
    qid = qubits2ids.setdefault(qubit, qid_count)
    if qid == qid_count:
        qid_count += 1
    return qid, qid_count
