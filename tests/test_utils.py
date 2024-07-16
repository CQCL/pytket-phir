##############################################################################
#
# Copyright (c) 2023-2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import json
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from wasmtime import wat2wasm

from pytket.phir.phirgen import WORDSIZE
from pytket.phir.phirgen_parallel import genphir_parallel
from pytket.phir.place_and_route import place_and_route
from pytket.phir.qtm_machine import QTM_MACHINES_MAP, QtmMachine
from pytket.phir.rebasing.rebaser import rebase_to_qtm_machine
from pytket.phir.sharding.sharder import Sharder
from pytket.qasm.qasm import circuit_from_qasm

if TYPE_CHECKING:
    from pytket.circuit import Circuit
    from pytket.phir.phirgen import JsonDict


class QasmFile(Enum):
    baby = auto()
    simple = auto()
    eztest = auto()
    baby_with_rollup = auto()
    big_gate = auto()
    simple_cond = auto()
    n10_test = auto()
    classical_hazards = auto()
    cond_1 = auto()
    barrier_complex = auto()
    cond_classical = auto()
    bv_n10 = auto()
    oned_brickwork_circuit_n20 = auto()
    qv20_0 = auto()
    parallelization_test = auto()
    tk2_same_angle = auto()
    tk2_diff_angles = auto()
    rxrz = auto()
    classical_ordering = auto()
    single_qubit_parallel_test = auto()
    exec_order_two_qubits = auto()
    rz_exec_order_three_qubits = auto()
    cond_barrier = auto()
    arbitrary_qreg_names = auto()
    group_ordering = auto()
    sleep = auto()


class WatFile(Enum):
    add = auto()
    testfile = auto()


def get_qasm_as_circuit(qasm_file: QasmFile) -> "Circuit":
    """Utility function to convert a QASM file to Circuit.

    Args:
        qasm_file: enum for a QASM file

    Returns:
        Corresponding tket circuit
    """
    this_dir = Path(Path(__file__).resolve()).parent
    return circuit_from_qasm(
        f"{this_dir}/data/qasm/{qasm_file.name}.qasm", maxwidth=WORDSIZE
    )


def get_phir_json(qasmfile: QasmFile, *, rebase: bool) -> "JsonDict":
    """Get the QASM file for the specified circuit."""
    qtm_machine = QtmMachine.H1
    circuit = get_qasm_as_circuit(qasmfile)
    if rebase:
        circuit = rebase_to_qtm_machine(circuit, qtm_machine)
    machine = QTM_MACHINES_MAP.get(qtm_machine)
    assert machine
    shards = Sharder(circuit).shard()
    placed = place_and_route(shards, machine)
    return json.loads(genphir_parallel(placed, machine))  # type: ignore[misc, no-any-return]


def get_wat_as_wasm_bytes(wat_file: WatFile) -> bytes:
    """Gets a given wat file, converted to WASM bytes by wasmtime."""
    this_dir = Path(Path(__file__).resolve()).parent
    return wat2wasm(
        Path(f"{this_dir}/data/wasm/{wat_file.name}.wat").read_text(encoding="utf-8")
    )
