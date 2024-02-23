##############################################################################
#
# Copyright (c) 2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json
from pathlib import Path

from pytket.circuit import Circuit
from pytket.phir.api import pytket_to_phir

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


def test_global_phase() -> None:
    """From https://github.com/CQCL/pytket-phir/issues/136 ."""
    this_dir = Path(Path(__file__).resolve()).parent
    with Path(f"{this_dir}/data/phase.json").open() as fp:
        circ = Circuit.from_dict(json.load(fp))

    phir = json.loads(pytket_to_phir(circ))
    assert phir["ops"][-7]["true_branch"] == [{"mop": "Skip"}]
