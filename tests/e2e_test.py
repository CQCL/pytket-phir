##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from phir.model import PHIRModel
from rich import print  # noqa: A004

from pytket.phir.machine import Machine, MachineTimings
from pytket.phir.phirgen import genphir
from pytket.phir.place_and_route import place_and_route
from pytket.phir.placement import placement_check
from pytket.phir.qtm_machine import QTM_DEFAULT_GATESET, QTM_MACHINES_MAP, QtmMachine
from pytket.phir.sharding.sharder import Sharder
from tests.test_utils import QasmFile, get_qasm_as_circuit

if __name__ == "__main__":
    machine = Machine(3, QTM_DEFAULT_GATESET, {1}, MachineTimings(3.0, 1.0, 2.0, 2.0))
    # force machine options for this test
    # machines normally don't like odd numbers of qubits
    machine.sq_options = {0, 1, 2}

    h11 = QTM_MACHINES_MAP[QtmMachine.H1]

    circuit = get_qasm_as_circuit(QasmFile.classical_hazards)
    sharder = Sharder(circuit)
    shards = sharder.shard()

    output = place_and_route(shards, h11)
    ez_ops_0 = [[0, 2], [1]]
    ez_ops_1 = [[0], [2]]
    state_0 = output[0][0]
    state_1 = output[1][0]
    assert placement_check(ez_ops_0, machine.tq_options, machine.sq_options, state_0)
    assert placement_check(ez_ops_1, machine.tq_options, machine.sq_options, state_1)
    shards_0 = output[0][1]
    shards_1 = output[1][1]
    for shard in shards_0:
        assert shard.ID in {0, 1}
    for shard in shards_1:
        assert shard.ID in {2, 3}
    cost_0 = output[0][2]
    cost_1 = output[1][2]
    assert cost_1 == 0.0

    phir_json = genphir(output)

    print(PHIRModel.model_validate_json(phir_json))  # type: ignore[misc]
