from pytket.phir.machine_class import Machine
from pytket.phir.placement import optimized_place
from pytket.phir.routing import transport_cost
from pytket.phir.sharding.sharder import Sharder
from pytket.phir.sharding.shards2ops import parse_shards_naive
from tests.sample_data import QasmFiles, get_qasm_as_circuit

if __name__ == "__main__":
    # Right now this is the achine we will use because the biggest test circuit is n=10
    # The placement algo also assumes that the trap will always be fully loaded
    # for example, if it is an n=10 trap, we will place and route as thought there are always 10 qubits  # noqa: E501
    machine = Machine(
        10,
        {0, 2, 4, 6, 8},
        3.0,
        1.0,
        2.0,
    )  # these are placeholder values
    circuit = get_qasm_as_circuit(QasmFiles.bv_n10)
    # check simple.qasm?
    sharder = Sharder(circuit)
    shards = sharder.shard()
    shard_set = set(shards)
    circuit_rep = parse_shards_naive(shard_set)
    print(f"Circuit:\n{circuit_rep}")  # noqa: T201
    initial_order = list(range(machine.size))
    layer_num = 0
    net_cost: float = 0.0
    for layer in circuit_rep:
        order = optimized_place(
            layer,
            machine.tq_options,
            machine.sq_options,
            machine.size,
            initial_order,
        )
        print(f"Order for layer {layer_num}: {layer}\n{order}")  # noqa: T201
        cost = transport_cost(initial_order, order, machine.qb_swap_time)
        print(f"Approx. Cost: {cost} us")  # noqa: T201
        layer_num += 1
        initial_order = order
        net_cost += cost
    print(f"Net Cost: {net_cost} us")  # noqa: T201
