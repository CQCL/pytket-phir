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
from pytket.qasm.qasm import circuit_from_qasm_str

from .test_utils import QasmFile, get_qasm_as_circuit


def test_classicalexpbox() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/86 ."""
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


def test_nested_arith() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/87 ."""
    circ = Circuit(1)
    a = circ.add_c_register("a", 2)
    b = circ.add_c_register("b", 2)
    c = circ.add_c_register("c", 3)
    circ.add_classicalexpbox_register(a + b // c, c.to_list())

    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][4] == {
        "cop": "=",
        "returns": ["c"],
        "args": [{"cop": "+", "args": ["a", {"cop": "/", "args": ["b", "c"]}]}],
    }


def test_arith_with_int() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/88 ."""
    circ = Circuit(1)
    a = circ.add_c_register("a", 2)
    circ.add_classicalexpbox_register(a << 1, a.to_list())

    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][2] == {
        "cop": "=",
        "returns": ["a"],
        "args": [{"cop": "<<", "args": ["a", 1]}],
    }


def test_bitwise_ops() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/91 ."""
    circ = Circuit(1)
    a = circ.add_c_register("a", 2)
    b = circ.add_c_register("b", 2)
    c = circ.add_c_register("c", 1)
    expr = a[0] ^ b[0]
    circ.add_classicalexpbox_bit(expr, [c[0]])

    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][4] == {
        "cop": "=",
        "returns": [["c", 0]],
        "args": [{"cop": "^", "args": [["a", 0], ["b", 0]]}],
    }


def test_conditional_barrier() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/119 ."""
    circ = get_qasm_as_circuit(QasmFile.cond_barrier)
    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][4] == {"//": "IF ([m[0], m[1]] == 0) THEN Barrier q[0], q[1];"}
    assert phir["ops"][5] == {
        "block": "if",
        "condition": {"cop": "==", "args": ["m", 0]},
        "true_branch": [{"meta": "barrier", "args": [["q", 0], ["q", 1]]}],
    }


def test_nested_bitwise_op() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/133 ."""
    circ = Circuit(4)
    a = circ.add_c_register("a", 4)
    b = circ.add_c_register("b", 1)
    circ.add_classicalexpbox_bit(a[0] ^ a[1] ^ a[2] ^ a[3], [b[0]])

    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][3] == {
        "cop": "=",
        "returns": [["b", 0]],
        "args": [
            {
                "cop": "^",
                "args": [
                    {
                        "cop": "^",
                        "args": [{"cop": "^", "args": [["a", 0], ["a", 1]]}, ["a", 2]],
                    },
                    ["a", 3],
                ],
            }
        ],
    }


def test_sleep_idle() -> None:
    """Ensure sleep from qasm gets converted to PHIR Idle Mop."""
    circ = get_qasm_as_circuit(QasmFile.sleep)
    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][7] == {"mop": "Idle", "args": [["q", 0]], "duration": [1.0, "s"]}


def test_multiple_sleep() -> None:
    """Ensure multiple sleep ops get converted correctly."""
    qasm = """
    OPENQASM 2.0;
    include "hqslib1_dev.inc";

    qreg q[2];

    sleep(1) q[0];
    sleep(2) q[1];
    """
    circ = circuit_from_qasm_str(qasm)
    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][2] == {"mop": "Idle", "args": [["q", 0]], "duration": [1.0, "s"]}
    assert phir["ops"][4] == {"mop": "Idle", "args": [["q", 1]], "duration": [2.0, "s"]}


def test_reordering_classical_conditional() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/150 ."""
    circuit = Circuit(1)

    ctrl = circuit.add_c_register(name="ctrl", size=1)
    meas = circuit.add_c_register(name="meas", size=1)

    circuit.add_c_setreg(1, ctrl)
    circuit.X(0, condition=ctrl[0])

    circuit.add_c_setreg(0, ctrl)
    circuit.X(0, condition=ctrl[0])

    circuit.Measure(
        qubit=circuit.qubits[0],
        bit=meas[0],
    )

    phir = json.loads(pytket_to_phir(circuit))

    assert phir["ops"][4] == {"args": [1], "cop": "=", "returns": [["ctrl", 0]]}
    assert phir["ops"][6] == {
        "block": "if",
        "condition": {"args": [["ctrl", 0], 1], "cop": "=="},
        "true_branch": [{"angles": None, "args": [["q", 0]], "qop": "X"}],
    }
    assert phir["ops"][8] == {"args": [0], "cop": "=", "returns": [["ctrl", 0]]}
    assert phir["ops"][10] == {
        "block": "if",
        "condition": {"args": [["ctrl", 0], 1], "cop": "=="},
        "true_branch": [{"angles": None, "args": [["q", 0]], "qop": "X"}],
    }


def test_conditional_measure() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/154 ."""
    c = Circuit(2, 2)
    c.H(0).H(1)
    c.Measure(0, 0)
    c.Measure(1, 1, condition_bits=[0], condition_value=1)
    phir = json.loads(pytket_to_phir(c))
    assert phir["ops"][-1] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["c", 0], 1]},
        "true_branch": [{"qop": "Measure", "returns": [["c", 1]], "args": [["q", 1]]}],
    }
