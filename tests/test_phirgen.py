##############################################################################
#
# Copyright (c) 2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json

from pytket.circuit import Bit, Circuit
from pytket.circuit.logic_exp import BitWiseOp, create_bit_logic_exp
from pytket.phir.api import pytket_to_phir
from pytket.phir.phirgen import WORDSIZE
from pytket.qasm.qasm import circuit_from_qasm_str
from pytket.unit_id import BitRegister

from .test_utils import QasmFile, get_qasm_as_circuit


def test_multiple_sleep() -> None:
    """Ensure multiple sleep ops get converted correctly."""
    qasm = """
    OPENQASM 2.0;
    include "hqslib1_dev.inc";

    qreg q[2];

    sleep(1) q[0];
    sleep(2) q[1];
    """
    circ = circuit_from_qasm_str(qasm, maxwidth=WORDSIZE)
    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][2] == {"mop": "Idle", "args": [["q", 0]], "duration": [1.0, "s"]}
    assert phir["ops"][4] == {"mop": "Idle", "args": [["q", 1]], "duration": [2.0, "s"]}


def test_simple_cond_classical() -> None:
    """Ensure conditional classical operation are correctly generated."""
    circ = get_qasm_as_circuit(QasmFile.simple_cond)
    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][-6] == {"//": "IF ([c[0]] == 1) THEN SetBits(1) z[0];"}
    assert phir["ops"][-5] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["c", 0], 1]},
        "true_branch": [{"cop": "=", "returns": [["z", 0]], "args": [1]}],
    }


def test_pytket_classical_only() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/61 ."""
    c = Circuit(1)
    a = c.add_c_register("a", 2)
    b = c.add_c_register("b", 3)

    c.add_c_copyreg(a, b)
    c.add_c_copybits([Bit("b", 2), Bit("a", 1)], [Bit("a", 0), Bit("b", 0)])
    c.add_c_copybits(
        [Bit("b", 2), Bit("a", 1)], [Bit("a", 0), Bit("b", 0)], condition=Bit("b", 1)
    )
    c.add_c_copybits(
        [Bit("a", 0), Bit("a", 1)],  # type: ignore[list-item] # overloaded function
        [Bit("b", 0), Bit("b", 1)],  # type: ignore[list-item] # overloaded function
        condition_bits=[Bit("b", 1), Bit("b", 2)],
        condition_value=2,
    )

    phir = json.loads(pytket_to_phir(c))

    assert phir["ops"][3] == {
        "cop": "=",
        "returns": [["b", 0], ["b", 1]],
        "args": [["a", 0], ["a", 1]],
    }
    assert phir["ops"][5] == {
        "cop": "=",
        "returns": [["a", 0], ["b", 0]],
        "args": [["b", 2], ["a", 1]],
    }
    assert phir["ops"][7] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["b", 1], 1]},
        "true_branch": [
            {"cop": "=", "returns": [["a", 0], ["b", 0]], "args": [["b", 2], ["a", 1]]}
        ],
    }
    assert phir["ops"][8] == {
        "//": "IF ([b[1], b[2]] == 2) THEN CopyBits a[0], a[1], b[0], b[1];"
    }
    assert phir["ops"][9] == {
        "block": "if",
        "condition": {
            "cop": "&",
            "args": [
                {"cop": "==", "args": [["b", 1], 0]},
                {"cop": "==", "args": [["b", 2], 1]},
            ],
        },
        "true_branch": [
            {"cop": "=", "returns": [["b", 0], ["b", 1]], "args": [["a", 0], ["a", 1]]}
        ],
    }


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
        "condition": {
            "cop": "&",
            "args": [
                {"cop": "==", "args": [["m", 0], 0]},
                {"cop": "==", "args": [["m", 1], 0]},
            ],
        },
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
    assert phir["ops"][-2] == {"//": "IF ([c[0]] == 1) THEN Measure q[1] --> c[1];"}
    assert phir["ops"][-1] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["c", 0], 1]},
        "true_branch": [{"qop": "Measure", "returns": [["c", 1]], "args": [["q", 1]]}],
    }


def test_conditional_classical_not() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/159 ."""
    circuit = Circuit()
    target_reg = circuit.add_c_register(BitRegister(name="target_reg", size=1))
    control_reg = circuit.add_c_register(BitRegister(name="control_reg", size=1))

    circuit.add_c_not(
        arg_in=target_reg[0], arg_out=target_reg[0], condition=control_reg[0]
    )

    phir = json.loads(pytket_to_phir(circuit))
    assert phir["ops"][-1] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["control_reg", 0], 1]},
        "true_branch": [
            {
                "cop": "=",
                "returns": [["target_reg", 0]],
                "args": [{"cop": "~", "args": [["target_reg", 0]]}],
            }
        ],
    }


def test_explicit_classical_ops() -> None:
    """Test explicit predicates and modifiers."""
    # From https://github.com/CQCL/tket/blob/a2f6fab8a57da8787dfae94764b7c3a8e5779024/pytket/tests/classical_test.py#L97-L101
    c = Circuit(0, 4)
    # predicates
    c.add_c_and(1, 2, 3)
    c.add_c_not(0, 1)
    c.add_c_xor(1, 2, 3)
    # modifiers
    c.add_c_and(2, 3, 3)
    c.add_c_or(0, 3, 0)
    phir = json.loads(pytket_to_phir(c))
    assert phir["ops"][1] == {"//": "AND c[1], c[2], c[3];"}
    assert phir["ops"][2] == {
        "cop": "=",
        "returns": [["c", 3]],
        "args": [{"cop": "&", "args": [["c", 1], ["c", 2]]}],
    }
    assert phir["ops"][3] == {"//": "NOT c[0], c[1];"}
    assert phir["ops"][4] == {
        "cop": "=",
        "returns": [["c", 1]],
        "args": [{"cop": "~", "args": [["c", 0]]}],
    }
    assert phir["ops"][5] == {"//": "XOR c[1], c[2], c[3];"}
    assert phir["ops"][6] == {
        "cop": "=",
        "returns": [["c", 3]],
        "args": [{"cop": "^", "args": [["c", 1], ["c", 2]]}],
    }
    assert phir["ops"][7] == {"//": "AND c[2], c[3];"}
    assert phir["ops"][8] == {
        "cop": "=",
        "returns": [["c", 3]],
        "args": [{"cop": "&", "args": [["c", 2], ["c", 3]]}],
    }
    assert phir["ops"][9] == {"//": "OR c[3], c[0];"}
    assert phir["ops"][10] == {
        "cop": "=",
        "returns": [["c", 0]],
        "args": [{"cop": "|", "args": [["c", 3], ["c", 0]]}],
    }


def test_multi_bit_ops() -> None:
    """Test classical ops added to the circuit via tket multi-bit ops."""
    # Test from https://github.com/CQCL/tket/blob/a2f6fab8a57da8787dfae94764b7c3a8e5779024/pytket/tests/classical_test.py#L107-L112
    c = Circuit(0, 4)
    c0 = c.add_c_register("c0", 3)
    c1 = c.add_c_register("c1", 4)
    c2 = c.add_c_register("c2", 5)
    # predicates
    c.add_c_and_to_registers(c0, c1, c2)
    c.add_c_not_to_registers(c1, c2)
    c.add_c_or_to_registers(c0, c1, c2)
    # modifier
    c.add_c_xor_to_registers(c2, c1, c2)
    # conditionals
    c.add_c_not_to_registers(c1, c2, condition=Bit("c0", 0))
    c.add_c_not_to_registers(c1, c1, condition=Bit("c0", 0))
    phir = json.loads(pytket_to_phir(c))
    assert phir["ops"][3] == {
        "//": "AND (*3) c0[0], c1[0], c2[0], c0[1], c1[1], c2[1], c0[2], c1[2], c2[2];"
    }
    assert phir["ops"][4] == {
        "cop": "=",
        "returns": ["c2"],
        "args": [{"cop": "&", "args": ["c0", "c1"]}],
    }
    assert phir["ops"][5] == {
        "//": "NOT (*4) c1[0], c2[0], c1[1], c2[1], c1[2], c2[2], c1[3], c2[3];"
    }
    assert phir["ops"][6] == {
        "cop": "=",
        "returns": ["c2"],
        "args": [{"cop": "~", "args": ["c1"]}],
    }
    assert phir["ops"][7] == {
        "//": "OR (*3) c0[0], c1[0], c2[0], c0[1], c1[1], c2[1], c0[2], c1[2], c2[2];"
    }
    assert phir["ops"][8] == {
        "cop": "=",
        "returns": ["c2"],
        "args": [{"cop": "|", "args": ["c0", "c1"]}],
    }
    assert phir["ops"][9] == {
        "//": "XOR (*4) c1[0], c2[0], c1[1], c2[1], c1[2], c2[2], c1[3], c2[3];"
    }
    assert phir["ops"][10] == {
        "cop": "=",
        "returns": ["c2"],
        "args": [{"cop": "^", "args": ["c1", "c2"]}],
    }
    assert phir["ops"][12] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["c0", 0], 1]},
        "true_branch": [
            {"cop": "=", "returns": ["c2"], "args": [{"cop": "~", "args": ["c1"]}]}
        ],
    }
    assert phir["ops"][14] == {
        "block": "if",
        "condition": {"cop": "==", "args": [["c0", 0], 1]},
        "true_branch": [
            {"cop": "=", "returns": ["c1"], "args": [{"cop": "~", "args": ["c1"]}]}
        ],
    }


def test_irregular_multibit_ops() -> None:
    """From https://github.com/CQCL/pytket-phir/pull/162#discussion_r1555807863 ."""
    c = Circuit()
    areg = c.add_c_register("a", 2)
    breg = c.add_c_register("b", 2)
    creg = c.add_c_register("c", 2)
    c.add_c_and_to_registers(areg, breg, creg)
    mbop = c.get_commands()[0].op
    c.add_gate(mbop, [areg[0], areg[1], breg[0], breg[1], creg[0], creg[1]])

    phir = json.loads(pytket_to_phir(c))
    assert phir["ops"][3] == {"//": "AND (*2) a[0], b[0], c[0], a[1], b[1], c[1];"}
    assert phir["ops"][4] == {
        "cop": "=",
        "returns": ["c"],
        "args": [{"cop": "&", "args": ["a", "b"]}],
    }
    assert phir["ops"][5] == {"//": "AND (*2) a[0], a[1], b[0], b[1], c[0], c[1];"}
    assert phir["ops"][6] == {
        "block": "sequence",
        "ops": [
            {
                "cop": "=",
                "returns": [["b", 0]],
                "args": [{"cop": "&", "args": [["a", 0], ["a", 1]]}],
            },
            {
                "cop": "=",
                "returns": [["c", 1]],
                "args": [{"cop": "&", "args": [["b", 1], ["c", 0]]}],
            },
        ],
    }


def test_nullary_ops() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/178 ."""
    c = Circuit(1, 1)
    exp1 = create_bit_logic_exp(BitWiseOp.ONE, [])
    c.H(0, condition=exp1)
    exp0 = create_bit_logic_exp(BitWiseOp.ZERO, [])
    c.H(0, condition=exp0)
    c.measure_all()
    phir = json.loads(pytket_to_phir(c))

    assert phir["ops"][4] == {
        "cop": "=",
        "returns": [["tk_SCRATCH_BIT", 0]],
        "args": [1],
    }
    assert phir["ops"][6] == {
        "cop": "=",
        "returns": [["tk_SCRATCH_BIT", 1]],
        "args": [0],
    }
    assert phir["ops"][8]["condition"] == {
        "cop": "==",
        "args": [["tk_SCRATCH_BIT", 0], 1],
    }
    assert phir["ops"][10]["condition"] == {
        "cop": "==",
        "args": [["tk_SCRATCH_BIT", 1], 1],  # evals to False
    }


def test_condition_multiple_bits() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/215 ."""
    n_bits = 3
    c = Circuit(1, n_bits)
    c.Rz(0.5, 0, condition_bits=list(range(n_bits)), condition_value=6)
    phir = json.loads(pytket_to_phir(c))

    assert phir["ops"][2] == {"//": "IF ([c[0], c[1], c[2]] == 6) THEN Rz(0.5) q[0];"}
    assert phir["ops"][3]["condition"] == {
        "cop": "&",
        "args": [
            {"cop": "==", "args": [["c", 0], 0]},
            {
                "cop": "&",
                "args": [
                    {"cop": "==", "args": [["c", 1], 1]},
                    {"cop": "==", "args": [["c", 2], 1]},
                ],
            },
        ],
    }
