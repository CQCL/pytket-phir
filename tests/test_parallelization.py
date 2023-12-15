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
    circuit = rebase_to_qtm_machine(circuit, qtm_machine.value)
    machine = QTM_MACHINES_MAP.get(qtm_machine)
    assert machine
    sharder = Sharder(circuit)
    shards = sharder.shard()
    placed = place_and_route(shards, machine)
    return json.loads(genphir_parallel(placed, machine))  # type: ignore[no-any-return]


def test_bv_n10() -> None:
    """Make sure the parallelization is happening properly for the test circuit."""
    actual = get_phir_json(QasmFile.parallelization_test)
    expected: dict[str, Any] = {
        "ops": [
            {"data": "qvar_define", "data_type": "qubits", "variable": "q", "size": 4},
            {"data": "cvar_define", "data_type": "u32", "variable": "c", "size": 4},
            {"//": "Parallel Rz(1)"},
            {
                "qop": "RZ",
                "angles": [[1.0], "pi"],
                "args": [["q", 0], ["q", 1], ["q", 2], ["q", 3]],
            },
            {"//": "Parallel PhasedX(0.5, 0.5)"},
            {
                "qop": "R1XY",
                "angles": [[0.5, 0.5], "pi"],
                "args": [["q", 0], ["q", 1], ["q", 2], ["q", 3]],
            },
            {"//": "Parallel RZZ"},
            {
                "block": "qparallel",
                "ops": [
                    {
                        "qop": "RZZ",
                        "angles": [[0.125], "pi"],
                        "args": [[["q", 0], ["q", 1]]],
                    },
                    {
                        "qop": "RZZ",
                        "angles": [[1.0], "pi"],
                        "args": [[["q", 2], ["q", 3]]],
                    },
                ],
            },
            {"mop": "Transport", "duration": [0.0, "ms"]},
            {
                "qop": "Measure",
                "args": [["q", 0], ["q", 1], ["q", 2], ["q", 3]],
                "returns": [["c", 0], ["c", 1], ["c", 2], ["c", 3]],
            },
            {"mop": "Transport", "duration": [0.0, "ms"]},
        ],
    }

    assert actual["ops"][7]["block"] == "qparallel"
    for op in expected["ops"][7]["ops"]:
        assert op in actual["ops"][7]["ops"]

    act_meas_op = actual["ops"][9]
    assert act_meas_op["qop"] == "Measure"
    assert sorted(act_meas_op["args"]) == expected["ops"][9]["args"]
    assert sorted(act_meas_op["returns"]) == expected["ops"][9]["returns"]
