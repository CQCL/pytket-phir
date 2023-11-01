from .shard import Shard


def parse_shards_naive(
    shards: set[Shard],
) -> tuple[list[list[list[int]]], list[list[Shard]]]:
    """Parse a set of shards and return a circuit representation for placement."""
    layers: list[list[list[int]]] = []
    shards_in_layer: list[list[Shard]] = []
    scheduled: set[int] = set()
    num_shards: int = len(shards)

    while len(scheduled) < num_shards:
        layer: list[list[int]] = []
        to_schedule: list[Shard] = []
        # get all the shards with no dependencies
        for shard in shards:
            s = shard
            deps = s.depends_upon
            # dependencies of the shard that have already been scheduled
            scheduled_deps = deps.intersection(scheduled)
            already_scheduled = s.ID in scheduled

            if scheduled_deps == deps and not already_scheduled:
                to_schedule.append(s)
        shards_in_layer.append(to_schedule)

        for shard in to_schedule:
            op: list[int] = []
            # if there are more than 2 qubits used, treat them all as parallel sq ops
            # one qubit will just be a single sq op
            # 3 or more will be 3 or more parallel sq ops
            if len(shard.qubits_used) != 2:  # noqa: PLR2004
                for qubit in shard.qubits_used:
                    op = qubit.index
                    layer.append(op)
            else:
                for qubit in shard.qubits_used:
                    op.append(qubit.index[0])
                layer.append(op)

            scheduled.add(shard.ID)

        layers.append(layer)

    return layers, shards_in_layer
