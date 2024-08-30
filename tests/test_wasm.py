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
from tempfile import NamedTemporaryFile

import pytest

from pytket.circuit import Circuit, Qubit
from pytket.phir.api import pytket_to_phir, qasm_to_phir
from pytket.phir.qtm_machine import QtmMachine
from pytket.qasm.qasm import QASMUnsupportedError
from pytket.wasm.wasm import WasmFileHandler

from .test_utils import WatFile, get_wat_as_wasm_bytes

logger = logging.getLogger(__name__)


def test_qasm_to_phir_with_wasm() -> None:
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

    phir_str = qasm_to_phir(qasm, QtmMachine.H1, wasm_bytes=wasm_bytes)
    phir = json.loads(phir_str)

    expected_metadata = {"ff_object": (f"WASM module uid: {wasm_uid}")}

    assert phir["ops"][21] == {
        "metadata": expected_metadata,
        "cop": "ffcall",
        "function": "add",
        "args": ["cr", "cs"],
        "returns": ["co"],
    }


def test_qasm_wasm_unsupported_reg_len() -> None:
    """Test that qasm containing calls to WASM with more than 32-bits fails."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";

    creg cr[33];

    cr = add(cr, cr);
    """

    wasm_bytes = get_wat_as_wasm_bytes(WatFile.add)

    with pytest.raises(
        QASMUnsupportedError,
        match="limited to at most 32-bit|try setting the `maxwidth` parameter",
    ):
        qasm_to_phir(qasm, QtmMachine.H1, wasm_bytes=wasm_bytes)


def test_pytket_with_wasm() -> None:
    """Test whether pytket works with WASM."""
    wasm_bytes = get_wat_as_wasm_bytes(WatFile.testfile)
    phir_str: str
    with NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm_bytes)
        wasm_file.flush()

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

        phir_str = pytket_to_phir(c, QtmMachine.H1)

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
    assert phir["ops"][8] == {
        "//": "IF ([c1[0]] == 1) THEN WASM_function='add_one' args=['c0'] returns=['c0'];"  # noqa: E501
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
                "args": ["c0"],
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


def test_pytket_wasm_unsupported_reg_len() -> None:
    """Test that pytket circuit calling WASM with more than 32-bits fails."""
    wasm_bytes = get_wat_as_wasm_bytes(WatFile.testfile)
    with NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm_bytes)
        wasm_file.flush()

        w = WasmFileHandler(wasm_file.name)

        c = Circuit(0, 33)
        c0 = c.add_c_register("c0", 33)

        with pytest.raises(ValueError, match="only registers of at most 32 bits"):
            c.add_wasm_to_reg("no_return", w, [c0], [])


def test_conditional_wasm() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/156 ."""
    wasm_bytes = get_wat_as_wasm_bytes(WatFile.testfile)
    with NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file:
        wasm_file.write(wasm_bytes)
        wasm_file.flush()

        w = WasmFileHandler(wasm_file.name)

        c = Circuit(1)
        areg = c.add_c_register("a", 2)
        breg = c.add_c_register("b", 1)
        c.H(0)
        c.Measure(Qubit(0), breg[0])
        c.add_wasm(
            funcname="add_one",
            filehandler=w,
            list_i=[1],
            list_o=[1],
            args=[areg[0], areg[1]],
            args_wasm=[0],
            condition_bits=[breg[0]],
            condition_value=1,
        )

    phir = json.loads(pytket_to_phir(c))

    assert phir["ops"][-2] == {
        "//": "IF ([b[0]] == 1) THEN WASM_function='add_one' args=['a'] returns=['a'];"
    }
    assert phir["ops"][-1]["true_branch"][0]["args"] == ["a"]
