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
    """Make sure the parallelization is happening for the tk2_same_angle circuit."""
    actual = get_phir_json_no_rebase(QasmFile.tk2_same_angle)
    op = actual["ops"][3]["qop"]
    args = actual["ops"][3]["args"]
    # Make sure the op is TK2
    assert op == "R2XXYYZZ"
    # Make sure the pairs of args are all in the same op
    assert len(args) == 2
    assert len(args[0]) == 2
    assert len(args[1]) == 2
    assert (["q", 0] in args[0]) ^ (["q", 0] in args[1])
    assert (["q", 1] in args[0]) ^ (["q", 1] in args[1])
    assert (["q", 2] in args[0]) ^ (["q", 2] in args[1])
    assert (["q", 3] in args[0]) ^ (["q", 3] in args[1])
    # Make sure the measurement is formatted correctly
    measure_args = actual["ops"][5]["args"]
    measure_returns = actual["ops"][5]["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert (measure_args.index(["q", 0])) == (measure_returns.index(["c", 0]))
    assert (measure_args.index(["q", 1])) == (measure_returns.index(["c", 1]))
    assert (measure_args.index(["q", 2])) == (measure_returns.index(["c", 2]))
    assert (measure_args.index(["q", 3])) == (measure_returns.index(["c", 3]))


def test_pll_tk2_diff_angles() -> None:
    """Make sure the parallelization is happening for the tk2_diff_angles circuit."""
    actual = get_phir_json_no_rebase(QasmFile.tk2_diff_angles)
    parqblock = actual["ops"][3]
    # Make sure there is a parallel block
    assert parqblock["block"] == "qparallel"
    # Make sure the block has 2 ops
    assert len(parqblock["ops"]) == 2
    # Make sure those ops are properly formatted TK2 gates
    tk2_0 = parqblock["ops"][0]
    tk2_1 = parqblock["ops"][1]
    assert tk2_0["qop"] == "R2XXYYZZ"
    assert tk2_1["qop"] == "R2XXYYZZ"
    assert len(tk2_0["args"][0]) == 2
    assert len(tk2_1["args"][0]) == 2
    assert (["q", 0] in tk2_0["args"][0]) ^ (["q", 0] in tk2_1["args"][0])
    assert (["q", 1] in tk2_0["args"][0]) ^ (["q", 1] in tk2_1["args"][0])
    assert (["q", 2] in tk2_0["args"][0]) ^ (["q", 2] in tk2_1["args"][0])
    assert (["q", 3] in tk2_0["args"][0]) ^ (["q", 3] in tk2_1["args"][0])
    # Make sure the measurement is formatted correctly
    measure_args = actual["ops"][5]["args"]
    measure_returns = actual["ops"][5]["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert (measure_args.index(["q", 0])) == (measure_returns.index(["c", 0]))
    assert (measure_args.index(["q", 1])) == (measure_returns.index(["c", 1]))
    assert (measure_args.index(["q", 2])) == (measure_returns.index(["c", 2]))
    assert (measure_args.index(["q", 3])) == (measure_returns.index(["c", 3]))
