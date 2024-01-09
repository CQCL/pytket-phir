##############################################################################
#
# Copyright (c) 2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import logging

from .test_utils import QasmFile, get_phir_json

logger = logging.getLogger(__name__)


def test_parallelization() -> None:
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
