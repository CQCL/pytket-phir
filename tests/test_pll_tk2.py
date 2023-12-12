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
from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFile, get_qasm_as_circuit

logger = logging.getLogger(__name__)


def get_phir_json_no_rebase(qasmfile: QasmFile) -> dict[str, Any]:
    """Get the QASM file for the specified circuit."""
    qtm_machine = QtmMachine.H1_1
    circuit = get_qasm_as_circuit(qasmfile)
    machine = QTM_MACHINES_MAP.get(qtm_machine)
    assert machine
    sharder = Sharder(circuit)
    shards = sharder.shard()
    placed = place_and_route(shards, machine)
    return json.loads(genphir_parallel(placed, machine))  # type: ignore[no-any-return]


def test_pll_tk2() -> None:
    """Make sure the parallelization is happening properly for the pll_test circuit."""
    actual = get_phir_json_no_rebase(QasmFile.tk2)
    expected = {
        "format": "PHIR/JSON",
        "version": "0.1.0",
        "metadata": {"source": "pytket-phir", "strict_parallelism": "true"},
        "ops": [
            {"data": "qvar_define", "data_type": "qubits", "variable": "q", "size": 4},
            {"data": "cvar_define", "data_type": "u32", "variable": "c", "size": 4},
            {"//": "Parallel TK2(0.159155, 0.159155, 0.159155)"},
            {
                "qop": "R2XXYYZZ",
                "angles": [
                    [0.15915494309189535, 0.15915494309189535, 0.15915494309189535],
                    "pi",
                ],
                "args": [[["q", 0], ["q", 1]], [["q", 2], ["q", 3]]],
            },
            {"mop": "Transport", "duration": [0.0, "ms"]},
            {"//": "Parallel R2XXYYZZ"},
            {
                "block": "qparallel",
                "ops": [
                    {
                        "qop": "R2XXYYZZ",
                        "angles": [
                            [
                                0.3183098861837907,
                                0.3183098861837907,
                                0.3183098861837907,
                            ],
                            "pi",
                        ],
                        "args": [[["q", 0], ["q", 1]]],
                    },
                    {
                        "qop": "R2XXYYZZ",
                        "angles": [
                            [
                                0.15915494309189535,
                                0.15915494309189535,
                                0.15915494309189535,
                            ],
                            "pi",
                        ],
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
    assert actual == expected
