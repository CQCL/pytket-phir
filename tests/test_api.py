##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import json
import logging
from tempfile import NamedTemporaryFile

import pytest
from phir.model import PHIRModel

from pytket.circuit import Bit, Circuit
from pytket.phir.api import pytket_to_phir, qasm_to_phir
from pytket.phir.qtm_machine import QtmMachine
from pytket.wasm.wasm import WasmFileHandler

from .test_utils import QasmFile, WatFile, get_qasm_as_circuit, get_wat_as_wasm_bytes

logger = logging.getLogger(__name__)


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(QasmFile.baby)
        phir = pytket_to_phir(circuit)
        PHIRModel.model_validate_json(phir)  # type: ignore[misc]

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_no_machine_all(self, test_file: QasmFile) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(test_file)

        match test_file:
            case QasmFile.big_gate:
                with pytest.raises(KeyError, match=r".*CnX.*"):
                    assert pytket_to_phir(circuit)
            case QasmFile.qv20_0:
                with pytest.raises(KeyError, match=r".*U3.*"):
                    assert pytket_to_phir(circuit)
            case _:
                phir = pytket_to_phir(circuit)
                PHIRModel.model_validate_json(phir)  # type: ignore[misc]

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_h1_1_all(self, test_file: QasmFile) -> None:
        """Standard case."""
        circuit = get_qasm_as_circuit(test_file)

        phir = pytket_to_phir(circuit, QtmMachine.H1_1)
        PHIRModel.model_validate_json(phir)  # type: ignore[misc]

    def test_pytket_classical_only(self) -> None:
        c = Circuit(1)
        a = c.add_c_register("a", 2)
        b = c.add_c_register("b", 3)

        c.add_c_copyreg(a, b)
        c.add_c_copybits([Bit("b", 2), Bit("a", 1)], [Bit("a", 0), Bit("b", 0)])

        phir = json.loads(pytket_to_phir(c))  # type: ignore[misc]

        assert phir["ops"][3] == {  # type: ignore[misc]
            "cop": "=",
            "returns": [["b", 0], ["b", 1]],
            "args": [["a", 0], ["a", 1]],
        }
        assert phir["ops"][5] == {  # type: ignore[misc]
            "cop": "=",
            "returns": [["a", 0], ["b", 0]],
            "args": [["b", 2], ["a", 1]],
        }

    def test_qasm_to_phir(self) -> None:
        """Test the qasm string entrypoint works."""
        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[3];
        h q;
        ZZ q[1],q[0];
        creg cr[3];
        measure q[0]->cr[0];
        measure q[1]->cr[0];
        """

        phir = qasm_to_phir(qasm, QtmMachine.H1_1)
        PHIRModel.model_validate_json(phir)  # type: ignore[misc]

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

        phir_str = qasm_to_phir(qasm, QtmMachine.H1_1, wasm_bytes=wasm_bytes)
        phir = json.loads(phir_str)  # type: ignore[misc]
        assert phir is not None  # type: ignore[misc]

        expected_metadata = {
            "ff_object": (
                "WASM module uid: 28c0194b91f1e24d6fc40ec480c026a5874661184"
                "bcd411a61bd5d5383df5180"
            )
        }

        assert phir["ops"][21] == {  # type: ignore[misc]
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "add",
            "args": ["cr", "cs"],
            "returns": ["co"],
        }

    def test_pytket_with_wasm(self) -> None:
        wasm_bytes = get_wat_as_wasm_bytes(WatFile.testfile)
        phir_str: str
        with NamedTemporaryFile(suffix=".wasm") as wasm_file:
            wasm_file.write(wasm_bytes)
            wasm_file.seek(0)
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

        PHIRModel.model_validate_json(phir_str)  # type: ignore[misc]
        phir = json.loads(phir_str)  # type: ignore[misc]

        expected_metadata = {
            "ff_object": (
                "WASM module uid: 3138ec2df84e13dcee5f3772555e93d4"
                "3de8f2e2a0937770c5959bca2da4fb10"
            )
        }

        assert phir["ops"][4] == {  # type: ignore[misc]
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "multi",
            "args": ["c0", "c1"],
            "returns": ["c2"],
        }
        assert phir["ops"][7] == {  # type: ignore[misc]
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "add_one",
            "args": ["c2"],
            "returns": ["c2"],
        }
        assert phir["ops"][9] == {  # type: ignore[misc]
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
        assert phir["ops"][12] == {  # type: ignore[misc]
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "no_return",
            "args": ["c2"],
        }
        assert phir["ops"][14] == {  # type: ignore[misc]
            "metadata": expected_metadata,
            "cop": "ffcall",
            "function": "no_parameters",
            "args": [],
            "returns": ["c2"],
        }
