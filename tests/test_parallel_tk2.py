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


def test_pll_tk2_same_angle() -> None:
    """Make sure the parallelization is correct for the tk2_same_angle circuit."""
    actual = get_phir_json_no_rebase(QasmFile.tk2_same_angle)
    # check args in ops
    op = actual["ops"][3]
    measure = actual["ops"][5]
    assert op["qop"] == "R2XXYYZZ"
    assert len(op["args"]) == 2
    assert len(op["args"][0]) == 2
    assert len(op["args"][1]) == 2
    # check measure
    assert len(measure["args"]) == len(measure["returns"]) == 4


def test_pll_tk2_diff_angles() -> None:
    """Make sure the parallelization is correct for the tk2_diff_angles circuit."""
    actual = get_phir_json_no_rebase(QasmFile.tk2_diff_angles)
    # check qparallel block
    block = actual["ops"][3]
    measure = actual["ops"][5]
    assert block["block"] == "qparallel"
    assert len(block["ops"]) == 2
    # check measure
    assert len(measure["args"]) == len(measure["returns"]) == 4
