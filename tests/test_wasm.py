##############################################################################
#
# Copyright (c) 2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import base64
import hashlib
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from pytket.circuit import Circuit
from pytket.phir.api import pytket_to_phir, qasm_to_phir
from pytket.phir.qtm_machine import QtmMachine
from pytket.wasm.wasm import WasmFileHandler

from .test_utils import WatFile, get_wat_as_wasm_bytes

logger = logging.getLogger(__name__)


class TestWASM:
    def test_qasm_to_phir_with_wasm(self) -> None:
        """Test the qasm string entrypoint works with WASM."""
        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[2];
        h q;
        ZZ q[1],q[0];
        creg cr[3];
        creg cs[3];
        creg co[3];
        measure q[0]->cr[0];
        measure q[1]->cr[1];

        cs = cr;
        co = add(cr, cs);
        """

        wasm_bytes = get_wat_as_wasm_bytes(WatFile.add)

        wasm_uid = hashlib.sha256(base64.b64encode(wasm_bytes)).hexdigest()

        phir_str = qasm_to_phir(qasm, QtmMachine.H1_1, wasm_bytes=wasm_bytes)
        phir = json.loads(phir_str)

        expected_metadata = {"ff_object": (f"WASM module uid: {wasm_uid}")}

        assert phir["ops"][21] == {
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "add",
            "args": ["cr", "cs"],
            "returns": ["co"],
        }

    @pytest.mark.order("first")
    def test_pytket_with_wasm(self) -> None:
        wasm_bytes = get_wat_as_wasm_bytes(WatFile.testfile)
        phir_str: str
        try:
            wasm_file = NamedTemporaryFile(suffix=".wasm", delete=False)
            wasm_file.write(wasm_bytes)
            wasm_file.flush()
            wasm_file.close()

            w = WasmFileHandler(wasm_file.name)

            c = Circuit(6, 6)
            c0 = c.add_c_register("c0", 3)
            c1 = c.add_c_register("c1", 4)
            c2 = c.add_c_register("c2", 5)

            c.add_wasm_to_reg("multi", w, [c0, c1], [c2])
            c.add_wasm_to_reg("add_one", w, [c2], [c2])
            c.add_wasm_to_reg("no_return", w, [c2], [])
            c.add_wasm_to_reg("no_parameters", w, [], [c2])

            c.add_wasm_to_reg("add_one", w, [c0], [c0], condition=c1[0])

            phir_str = pytket_to_phir(c, QtmMachine.H1_1)
        finally:
            Path.unlink(Path(wasm_file.name))

        phir = json.loads(phir_str)

        expected_metadata = {"ff_object": (f"WASM module uid: {w!s}")}

        assert phir["ops"][4] == {
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "multi",
            "args": ["c0", "c1"],
            "returns": ["c2"],
        }
        assert phir["ops"][7] == {
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "add_one",
            "args": ["c2"],
            "returns": ["c2"],
        }
        assert phir["ops"][9] == {
            "block": "if",
            "condition": {"cop": "==", "args": [["c1", 0], 1]},
            "true_branch": [
                {
                    "metadata": expected_metadata,
                    "cop": "ffcall",
                    "returns": ["c0"],
                    "function": "add_one",
                    "args": ["c1", "c0"],
                }
            ],
        }
        assert phir["ops"][12] == {
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "no_return",
            "args": ["c2"],
        }
        assert phir["ops"][15] == {
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "no_parameters",
            "args": [],
            "returns": ["c2"],
        }
