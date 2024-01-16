##############################################################################
#
# Copyright (c) 2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json

from pytket.circuit import Circuit
from pytket.phir.api import pytket_to_phir


class TestPhirGen:
    def test_classicalexpbox(self) -> None:
        """From https://github.com/CQCL/pytket-phir/issues/86."""
        circ = Circuit(1)
        a = circ.add_c_register("a", 2)
        b = circ.add_c_register("b", 2)
        c = circ.add_c_register("c", 3)
        circ.add_classicalexpbox_register(a + b, c.to_list())

        phir = json.loads(pytket_to_phir(circ))
        assert phir["ops"][4] == {
            "cop": "=",
            "returns": ["c"],
            "args": [{"cop": "+", "args": ["a", "b"]}],
        }