from pytket.phir.machine_class import Machine
from pytket.phir.place_and_route import place_and_route
from pytket.phir.placement import placement_check
from tests.sample_data import QasmFiles

if __name__ == "__main__":
    machine = Machine(
        3,
        {1},
        3.0,
        1.0,
        2.0,
    )
    # force machine options for this test
    # machines normally don't like odd numbers of qubits
    machine.sq_options = {0, 1, 2}
    # The type: ignores in this file are because mypy doesn't like the return type of place and route,  # noqa: E501
    # list[triple(list[int], list[Shard], float)]
    output = place_and_route(machine, QasmFiles.eztest)  # type: ignore [misc]
    # print(output)
    ez_ops_0 = [[0, 2], [1]]
    ez_ops_1 = [[0], [2]]
    state_0 = output[0][0]  # type: ignore [misc]
    state_1 = output[1][0]  # type: ignore [misc]
    assert placement_check(ez_ops_0, machine.tq_options, machine.sq_options, state_0)  # type: ignore [misc]
    assert placement_check(ez_ops_1, machine.tq_options, machine.sq_options, state_1)  # type: ignore [misc]
    shards_0 = output[0][1]  # type: ignore [misc]
    shards_1 = output[1][1]  # type: ignore [misc]
    for shard in shards_0:  # type: ignore [misc]
        assert shard.ID in {0, 1}  # type: ignore [misc]
    for shard in shards_1:  # type: ignore [misc]
        assert shard.ID in {2, 3}  # type: ignore [misc]
    cost_0 = output[0][2]  # type: ignore [misc]
    cost_1 = output[1][2]  # type: ignore [misc]
    assert cost_0 == 2.0  # type: ignore [misc]
    assert cost_1 == 0.0  # type: ignore [misc]
