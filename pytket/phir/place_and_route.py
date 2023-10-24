from pytket.phir.machine import Machine
from pytket.phir.placement import optimized_place
from pytket.phir.routing import transport_cost
from pytket.phir.sharding.shard import Cost, Layer, Ordering, Shard
from pytket.phir.sharding.shards2ops import parse_shards_naive


def place_and_route(
    machine: Machine,
    shards: list[Shard],
) -> list[tuple[Ordering, Layer, Cost]]:
    """Get all the routing info needed for PHIR generation."""
    shard_set = set(shards)
    circuit_rep, shard_layers = parse_shards_naive(shard_set)
    if machine:
        initial_order = list(range(machine.size))
    layer_num = 0
    orders: list[Ordering] = []
    layer_costs: list[Cost] = []
    net_cost: float = 0.0
    if machine:
        for layer in circuit_rep:
            order = optimized_place(
                layer,
                machine.tq_options,
                machine.sq_options,
                machine.size,
                initial_order,
            )
            orders.append(order)
            cost = transport_cost(initial_order, order, machine.qb_swap_time)
            layer_num += 1
            initial_order = order
            layer_costs.append(cost)
            net_cost += cost
    else:
        # If no machine object specified,
        # generic lists of qubits with no placement and no routing costs,
        # only the shards

        # If needed later, write a helper to find the number
        # of qubits needed in the circuit

        for layer in circuit_rep:  # noqa: B007
            orders.append([])
            layer_costs.append(0)

    # don't need a custom error for this, "strict" parameter will throw error if needed
    return list(zip(orders, shard_layers, layer_costs, strict=True))
