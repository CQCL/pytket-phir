##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json
import logging
from typing import Any

from pytket.phir.phirgen_parallel import genphir_parallel
from pytket.phir.place_and_route import place_and_route
from pytket.phir.qtm_machine import QTM_MACHINES_MAP, QtmMachine
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine
from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFile, get_qasm_as_circuit

logger = logging.getLogger(__name__)


def get_phir_json(qasmfile: QasmFile) -> dict[str, Any]:
    """Get the QASM file for the specified circuit."""
    qtm_machine = QtmMachine.H1_1
    circuit = get_qasm_as_circuit(qasmfile)
    circuit = rebase_to_qtm_machine(circuit, qtm_machine.value, 0)
    machine = QTM_MACHINES_MAP.get(qtm_machine)
    assert machine
    sharder = Sharder(circuit)
    shards = sharder.shard()
    placed = place_and_route(shards, machine)
    return json.loads(genphir_parallel(placed, machine))  # type: ignore[no-any-return]


def test_bv_n10() -> None:
    """Make sure the parallelization is happening properly for the test circuit."""
    actual = get_phir_json(QasmFile.parallelization_test)
    parallel_rz1 = actual["ops"][3]
    assert parallel_rz1["qop"] == "RZ"
    qubits = [["q", 0], ["q", 1], ["q", 2], ["q", 3]]
    for qubit in qubits:
        assert qubit in parallel_rz1["args"]
    parallel_phasedx = actual["ops"][5]
    assert parallel_phasedx["qop"] == "R1XY"
    for qubit in qubits:
        assert qubit in parallel_phasedx["args"]
    block = actual["ops"][7]
    assert block["block"] == "qparallel"
    assert len(block["ops"]) == 2
    qop0 = block["ops"][0]
    qop1 = block["ops"][1]
    assert qop0["qop"] == qop1["qop"] == "RZZ"
    assert len(qop0["args"][0]) == len(qop1["args"][0]) == 2
    q01_first = (["q", 0] in qop0["args"][0]) and (["q", 1] in qop0["args"][0])
    q01_second = (["q", 0] in qop1["args"][0]) and (["q", 1] in qop1["args"][0])
    q23_first = (["q", 2] in qop0["args"][0]) and (["q", 3] in qop0["args"][0])
    q23_second = (["q", 2] in qop1["args"][0]) and (["q", 3] in qop1["args"][0])
    assert (q01_first and q23_second) ^ (q23_first and q01_second)
    measure = actual["ops"][9]
    measure_args = measure["args"]
    measure_returns = measure["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert measure_args.index(["q", 0]) == measure_returns.index(["c", 0])
    assert measure_args.index(["q", 1]) == measure_returns.index(["c", 1])
    assert measure_args.index(["q", 2]) == measure_returns.index(["c", 2])
    assert measure_args.index(["q", 3]) == measure_returns.index(["c", 3])
