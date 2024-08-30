##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import logging

from .test_utils import QasmFile, get_phir_json

logger = logging.getLogger(__name__)


def test_parallelization() -> None:
    """Make sure the parallelization is happening properly for the test circuit."""
    phir = get_phir_json(QasmFile.parallelization_test, rebase=True)

    # Make sure The parallel RZ and R1XY gates have the correct arguments
    parallel_rz1 = phir["ops"][3]
    assert parallel_rz1["qop"] == "RZ"
    qubits = [["q", 0], ["q", 1], ["q", 2], ["q", 3]]
    for qubit in qubits:
        assert qubit in parallel_rz1["args"]
    parallel_phasedx = phir["ops"][5]
    assert parallel_phasedx["qop"] == "R1XY"
    for qubit in qubits:
        assert qubit in parallel_phasedx["args"]

    # Make sure the parallel block is properly formatted
    block = phir["ops"][7]
    assert block["block"] == "qparallel"
    assert len(block["ops"]) == 2
    qop0 = block["ops"][0]
    qop1 = block["ops"][1]
    assert qop0["qop"] == qop1["qop"] == "RZZ"

    # Make sure the ops within the parallel block have the correct arguments
    assert len(qop0["args"][0]) == len(qop1["args"][0]) == 2
    q01_fst = (["q", 0] in qop0["args"][0]) and (["q", 1] in qop0["args"][0])
    q01_snd = (["q", 0] in qop1["args"][0]) and (["q", 1] in qop1["args"][0])
    q23_fst = (["q", 2] in qop0["args"][0]) and (["q", 3] in qop0["args"][0])
    q23_snd = (["q", 2] in qop1["args"][0]) and (["q", 3] in qop1["args"][0])
    assert (q01_fst and q23_snd) != (q23_fst and q01_snd)

    # Make sure the measure op is properly formatted
    measure = phir["ops"][9]
    measure_args = measure["args"]
    measure_returns = measure["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert measure_args.index(["q", 0]) == measure_returns.index(["c", 0])
    assert measure_args.index(["q", 1]) == measure_returns.index(["c", 1])
    assert measure_args.index(["q", 2]) == measure_returns.index(["c", 2])
    assert measure_args.index(["q", 3]) == measure_returns.index(["c", 3])


def test_parallel_subcommand_relative_ordering() -> None:
    """Make sure the proper relative ordering of sub-commands is preserved."""
    phir = get_phir_json(QasmFile.rxrz, rebase=True)
    # make sure it is ordered like the qasm file
    ops = phir["ops"]
    sc1 = ops[3]
    sc2 = ops[5]
    sc3 = ops[7]
    sc4 = ops[9]
    assert sc1["qop"] == "RZ"
    assert sc1["angles"] == [[0.5], "pi"]
    assert sc2["qop"] == "R1XY"
    assert sc2["angles"] == [[3.5, 0.0], "pi"]
    assert sc3["qop"] == "R1XY"
    assert sc3["angles"] == [[0.5, 0.0], "pi"]
    assert sc4["qop"] == "RZ"
    assert sc4["angles"] == [[3.5], "pi"]


def test_single_qubit_circuit_with_parallel() -> None:
    """Make sure there are no parallel blocks present in the 1qubit circuit."""
    phir_with_parallel_phirgen = get_phir_json(
        QasmFile.single_qubit_parallel_test, rebase=True
    )
    phir_with_standard_phirgen = get_phir_json(
        QasmFile.single_qubit_parallel_test, rebase=False
    )
    assert len(phir_with_parallel_phirgen) == len(phir_with_standard_phirgen)
    # since the rebasing converts to the native gate set,
    # the names and angle foramts of the qops will not match.
    # for example Ry gets converted to R1XY
    # compare angles and args instead

    ops = (3, 5, 7, 12, 14, 16)

    assert phir_with_parallel_phirgen["ops"][9] == {
        "meta": "barrier",
        "args": [["q", 0]],
    }

    for i, qop in zip(ops, ("R1XY", "RZ", "R1XY", "R1XY", "RZ", "R1XY"), strict=True):
        assert phir_with_parallel_phirgen["ops"][i]["qop"] == qop

    for i, qop in zip(ops, ("RY", "RZ", "RY", "RY", "RZ", "RY"), strict=True):
        assert phir_with_standard_phirgen["ops"][i]["qop"] == qop

    for i in ops:
        assert (
            phir_with_parallel_phirgen["ops"][i]["args"]
            == phir_with_standard_phirgen["ops"][i]["args"]
        )


def test_three_qubit_rz_exec_order_preserved() -> None:
    """Test that the order of gating is preserved in a 3 qubit circuit with RZ gates."""
    phir = get_phir_json(QasmFile.rz_exec_order_three_qubits, rebase=True)
    # verify that the parallel RZ gates are executed before the second R1XY gate
    assert phir["ops"][8] == {
        "qop": "R1XY",
        "angles": [[0.5, 0.5], "pi"],
        "args": [["q", 0]],
    }
    assert phir["ops"][10] == {
        "block": "qparallel",
        "ops": [
            {"qop": "RZ", "angles": [[0.5], "pi"], "args": [["q", 1]]},
            {"qop": "RZ", "angles": [[1.5], "pi"], "args": [["q", 2]]},
        ],
    }
    assert phir["ops"][12] == {
        "qop": "R1XY",
        "angles": [[0.5, 0.5], "pi"],
        "args": [["q", 2]],
    }


def test_two_qubit_exec_order_preserved() -> None:
    """Test that the order of gating in preserved in a 2 qubit circuit."""
    phir = get_phir_json(QasmFile.exec_order_two_qubits, rebase=True)

    assert phir["ops"][16] == {"meta": "barrier", "args": [["q", 0], ["q", 1]]}
    # for this test, verify that the RX gates are NOT parallelized
    # in the following section of the qasm file (lines 11-13):
    # rx(3.5*pi) q[0];
    assert phir["ops"][19] == {
        "qop": "R1XY",
        "angles": [[3.5, 0.0], "pi"],
        "args": [["q", 0]],
    }
    # rz(3.5*pi) q[1];
    assert phir["ops"][21] == {"qop": "RZ", "angles": [[3.5], "pi"], "args": [["q", 1]]}
    # rx(1.0*pi) q[1];
    assert phir["ops"][25] == {
        "qop": "R1XY",
        "angles": [[1.0, 0.0], "pi"],
        "args": [["q", 1]],
    }


def test_group_ordering() -> None:
    """Test that groups are in the right order when the group number can decrement."""
    phir = get_phir_json(QasmFile.group_ordering, rebase=True)
    block = phir["ops"][3]
    assert block["block"] == "qparallel"
    assert block["ops"][0] == {
        "qop": "R1XY",
        "angles": [[0.5, 0.0], "pi"],
        "args": [["q", 0]],
    }
    assert block["ops"][1] == {
        "qop": "R1XY",
        "angles": [[3.5, 0.5], "pi"],
        "args": [["q", 1]],
    }
    assert phir["ops"][5] == {
        "qop": "R1XY",
        "angles": [[0.5, 0.0], "pi"],
        "args": [["q", 0]],
    }
    assert phir["ops"][7] == {"qop": "RZ", "angles": [[1.0], "pi"], "args": [["q", 1]]}
    assert phir["ops"][9] == {
        "qop": "R1XY",
        "angles": [[3.5, 0.5], "pi"],
        "args": [["q", 1]],
    }
