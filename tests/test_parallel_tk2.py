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


def test_pll_tk2_same_angle() -> None:
    """Make sure the parallelization is correct for the tk2_same_angle circuit."""
    phir = get_phir_json(QasmFile.tk2_same_angle, rebase=False)

    # Check that the op is properly formatted
    op = phir["ops"][3]
    measure = phir["ops"][5]
    assert op["qop"] == "R2XXYYZZ"

    # Check that the args are properly formatted
    assert len(op["args"]) == 2
    assert len(op["args"][0]) == len(op["args"][1]) == 2
    q01_first = (["q", 0] in op["args"][0]) and (["q", 1] in op["args"][0])
    q01_second = (["q", 0] in op["args"][1]) and (["q", 1] in op["args"][1])
    q23_first = (["q", 2] in op["args"][0]) and (["q", 3] in op["args"][0])
    q23_second = (["q", 2] in op["args"][1]) and (["q", 3] in op["args"][1])
    assert (q01_first and q23_second) != (q23_first and q01_second)

    # Check that the measure op is properly formatted
    measure_args = measure["args"]
    measure_returns = measure["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert measure_args.index(["q", 0]) == measure_returns.index(["c", 0])
    assert measure_args.index(["q", 1]) == measure_returns.index(["c", 1])
    assert measure_args.index(["q", 2]) == measure_returns.index(["c", 2])
    assert measure_args.index(["q", 3]) == measure_returns.index(["c", 3])


def test_pll_tk2_diff_angles() -> None:
    """Make sure the parallelization is correct for the tk2_diff_angles circuit."""
    phir = get_phir_json(QasmFile.tk2_diff_angles, rebase=False)

    # Check that the qparallel block is properly formatted
    block = phir["ops"][3]
    measure = phir["ops"][5]
    assert block["block"] == "qparallel"
    assert len(block["ops"]) == 2

    # Check that the individual ops are properly formatted
    qop0 = block["ops"][0]
    qop1 = block["ops"][1]
    assert qop0["qop"] == qop1["qop"] == "R2XXYYZZ"
    assert len(qop0["args"][0]) == len(qop1["args"][0]) == 2
    q01_first = (["q", 0] in qop0["args"][0]) and (["q", 1] in qop0["args"][0])
    q01_second = (["q", 0] in qop1["args"][0]) and (["q", 1] in qop1["args"][0])
    q23_first = (["q", 2] in qop0["args"][0]) and (["q", 3] in qop0["args"][0])
    q23_second = (["q", 2] in qop1["args"][0]) and (["q", 3] in qop1["args"][0])
    assert (q01_first and q23_second) != (q23_first and q01_second)

    # Check that the measure op is properly foramtted
    measure_args = measure["args"]
    measure_returns = measure["returns"]
    assert len(measure_args) == len(measure_returns) == 4
    assert measure_args.index(["q", 0]) == measure_returns.index(["c", 0])
    assert measure_args.index(["q", 1]) == measure_returns.index(["c", 1])
    assert measure_args.index(["q", 2]) == measure_returns.index(["c", 2])
    assert measure_args.index(["q", 3]) == measure_returns.index(["c", 3])
