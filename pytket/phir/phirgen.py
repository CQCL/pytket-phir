import json
import logging
from typing import Any

from phir.model import PHIRModel
from pytket.circuit import Command

from .sharding.shard import Cost, Layer, Ordering

logger = logging.getLogger(__name__)

tket_op_to_phir = {
    "CX":       "CX",
    "CY":       "CY",
    "CZ":       "CZ",
    "H":        "H",
    "Measure":  "Measure",
    "noop":     "I",
    "PhasedX":  "R1XY",
    "Reset":    "Reset",  # TODO(kartik): confirm
    "Rx":       "RX",
    "Ry":       "RY",
    "Rz":       "RZ",
    "S":        "SZ",
    "Sdg":      "SZdg",
    "SWAP":     "SWAP",
    "SX":       "SX",
    "SXdg":     "SXdg",
    "T":        "T",
    "Tdg":      "Tdg",
    "TK2":      "R2XXYYZZ",
    "U1":       "RZ",
    "V":        "SX",
    "Vdg":      "SXdg",
    "X":        "X",
    "XXPhase":  "RXX",
    "Y":        "Y",
    "YYPhase":  "RYY",
    "Z":        "Z",
    "ZZMax":    "SZZ",
    "ZZPhase":  "RZZ",
}  # fmt: skip


def write_cmd(cmd: Command, ops: list[dict[str, Any]]) -> None:
    """Write a pytket command to PHIR qop.

    Args:
        cmd: pytket command obtained from pytket-phir
        ops: the list of ops to append to
    """
    gate_str = cmd.op.get_name().split("(", 1)[0]
    try:
        gate = tket_op_to_phir[gate_str]
    except KeyError:
        if not cmd.op.is_gate():  # TODO(kartik): convert these gates as well
            gate = gate_str
        else:
            raise
    angles = (cmd.op.params, "pi") if cmd.op.is_gate() and cmd.op.params else None

    qop: dict[str, Any] = {
        "angles": angles,
        "qop": gate,
        "args": [],
    }
    for qbit in cmd.args:
        qop["args"].append([qbit.reg_name, qbit.index[0]])
        if gate == "Measure":
            break
    if cmd.bits:
        qop["returns"] = []
        for cbit in cmd.bits:
            qop["returns"].append([cbit.reg_name, cbit.index[0]])
    ops.extend(({"//": str(cmd)}, qop))


def genphir(inp: list[tuple[Ordering, Layer, Cost]]) -> str:
    """Convert a list of shards to the equivalent PHIR.

    Args:
        inp: list of shards
    """
    phir: dict[str, Any] = {
        "format": "PHIR/JSON",
        "version": "0.1.0",
        "metadata": {"source": "pytket-phir"},
    }
    ops: list[dict[str, Any]] = []

    qbits = set()
    cbits = set()
    for _orders, shard_layer, layer_cost in inp:
        for shard in shard_layer:
            qbits |= shard.qubits_used
            cbits |= shard.bits_read | shard.bits_written
            for sub_commands in shard.sub_commands.values():
                for sc in sub_commands:
                    write_cmd(sc, ops)
            write_cmd(shard.primary_command, ops)
        ops.append(
            {
                "mop": "Transport",
                "duration": (layer_cost, "ms"),
            },
        )

    # TODO(kartik): this may not always be accurate
    qvar_dim: dict[str, int] = {}
    for qbit in qbits:
        qvar_dim.setdefault(qbit.reg_name, 0)
        qvar_dim[qbit.reg_name] += 1

    cvar_dim: dict[str, int] = {}
    for cbit in cbits:
        cvar_dim.setdefault(cbit.reg_name, 0)
        cvar_dim[cbit.reg_name] += 1

    decls: list[dict[str, str | int]] = [
        {
            "data": "qvar_define",
            "data_type": "qubits",
            "variable": q,
            "size": d,
        }
        for q, d in qvar_dim.items()
    ]

    decls += [
        {
            "data": "cvar_define",
            "variable": c,
            "size": d,
        }
        for c, d in cvar_dim.items()
    ]

    phir["ops"] = decls + ops
    PHIRModel.model_validate(phir)
    return json.dumps(phir)
