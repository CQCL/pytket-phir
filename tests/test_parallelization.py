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
    frst_sc = ops[3]
    scnd_sc = ops[5]
    thrd_sc = ops[7]
    frth_sc = ops[9]
    assert frst_sc["qop"] == "RZ"
    assert frst_sc["angles"] == [[0.5], "pi"]
    assert scnd_sc["qop"] == "R1XY"
    assert scnd_sc["angles"] == [[3.5, 0.0], "pi"]
    assert thrd_sc["qop"] == "R1XY"
    assert thrd_sc["angles"] == [[0.5, 0.0], "pi"]
    assert frth_sc["qop"] == "RZ"
    assert frth_sc["angles"] == [[3.5], "pi"]
