##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import json
import logging
from collections.abc import Sequence
from typing import Any

import pytket.circuit as tk
from phir.model import PHIRModel
from pytket.circuit.logic_exp import RegWiseOp
from pytket.unit_id import UnitID

from .sharding.shard import Cost, Ordering, ShardLayer

logger = logging.getLogger(__name__)

UINTMAX = 2**32 - 1

tket_gate_to_phir = {
    tk.OpType.Reset:    "Init",
    tk.OpType.Measure:  "Measure",
    tk.OpType.noop:     "I",

    tk.OpType.CX:       "CX",
    tk.OpType.CY:       "CY",
    tk.OpType.CZ:       "CZ",
    tk.OpType.H:        "H",
    tk.OpType.PhasedX:  "R1XY",
    tk.OpType.Rx:       "RX",
    tk.OpType.Ry:       "RY",
    tk.OpType.Rz:       "RZ",
    tk.OpType.S:        "SZ",
    tk.OpType.Sdg:      "SZdg",
    tk.OpType.SWAP:     "SWAP",
    tk.OpType.SX:       "SX",
    tk.OpType.SXdg:     "SXdg",
    tk.OpType.T:        "T",
    tk.OpType.Tdg:      "Tdg",
    tk.OpType.TK2:      "R2XXYYZZ",
    tk.OpType.U1:       "RZ",
    tk.OpType.V:        "SX",
    tk.OpType.Vdg:      "SXdg",
    tk.OpType.X:        "X",
    tk.OpType.XXPhase:  "RXX",
    tk.OpType.Y:        "Y",
    tk.OpType.YYPhase:  "RYY",
    tk.OpType.Z:        "Z",
    tk.OpType.ZZMax:    "SZZ",
    tk.OpType.ZZPhase:  "RZZ",
}  # fmt: skip


def arg_to_bit(arg: UnitID) -> list[str | int]:
    """Convert tket arg to Bit."""
    return [arg.reg_name, arg.index[0]]


def assign_cop(into: str | list[str | int], what: Sequence[int]) -> dict[str, Any]:
    """PHIR for assign classical operation."""
    return {
        "cop": "=",
        "returns": [into],
        "args": what,
    }


def convert_subcmd(op: tk.Op, cmd: tk.Command) -> dict[str, Any]:
    """Return PHIR dict give op and its arguments."""
    if op.is_gate():
        try:
            gate = tket_gate_to_phir[op.type]
        except KeyError:
            logging.exception("Gate %s unsupported by PHIR", op.get_name())
            raise
        angles = (op.params, "pi") if op.params else None
        qop: dict[str, Any]
        match gate:
            case "Measure":
                qop = {
                    "qop": gate,
                    "returns": [arg_to_bit(cmd.bits[0])],
                    "args": [arg_to_bit(cmd.args[0])],
                }

            case "R2XXYYZZ":  # three-qubit gate
                qop = {
                    "qop": gate,
                    "angles": angles,
                    "args": [
                        [
                            arg_to_bit(cmd.qubits[0]),
                            arg_to_bit(cmd.qubits[1]),
                            arg_to_bit(cmd.qubits[2]),
                        ]
                    ],
                }

            case (
                "CX"
                | "CY"
                | "CZ"
                | "RXX"
                | "RYY"
                | "RZZ"
                | "SXX"
                | "SXXdg"
                | "SYY"
                | "SYYdg"
                | "SZZ"
                | "SZZdg"
                | "SWAP"
            ):  # two-qubit gates
                qop = {
                    "qop": gate,
                    "angles": angles,
                    "args": [[arg_to_bit(cmd.qubits[0]), arg_to_bit(cmd.qubits[1])]],
                }
            case _:  # single-qubit gates
                qop = {
                    "qop": gate,
                    "angles": angles,
                    "args": [arg_to_bit(cmd.qubits[0])],
                }
        return qop

    match op:  # non-quantum op
        case tk.SetBitsOp():
            return assign_cop(arg_to_bit(cmd.bits[0]), op.values)

        case _:
            # TODO(kartik): NYI
            # https://github.com/CQCL/pytket-phir/issues/25
            raise NotImplementedError


def append_cmd(cmd: tk.Command, ops: list[dict[str, Any]]) -> None:
    """Convert a pytket command to a PHIR command and append to `ops`.

    Args:
        cmd: pytket command obtained from pytket-phir
        ops: the list of ops to append to
    """
    ops.append({"//": str(cmd)})
    if cmd.op.is_gate():
        ops.append(convert_subcmd(cmd.op, cmd))
    else:
        op: dict[str, Any] | None = None
        match cmd.op:
            case tk.SetBitsOp():
                op = convert_subcmd(cmd.op, cmd)

            case tk.BarrierOp():
                # TODO(kartik): confirm with Ciaran/spec
                # https://github.com/CQCL/phir/blob/main/spec.md
                logger.debug("Skipping Barrier instruction")

            case tk.Conditional():  # where the condition is equality check
                op = {
                    "block": "if",
                    "condition": {
                        "cop": "==",
                        "args": [
                            arg_to_bit(cmd.args[0])
                            if cmd.op.width == 1
                            else cmd.args[0].reg_name,
                            cmd.op.value,
                        ],
                    },
                    "true_branch": [convert_subcmd(cmd.op.op, cmd)],
                }

            case tk.RangePredicateOp():  # where the condition is a range
                cond: dict[str, Any]
                match cmd.op.lower, cmd.op.upper:
                    case l, u if l == u:
                        cond = {
                            "cop": "==",
                            "args": [cmd.args[0].reg_name, u],
                        }
                    case l, u if u == UINTMAX:
                        cond = {
                            "cop": ">=",
                            "args": [cmd.args[0].reg_name, l],
                        }
                    case 0, u:
                        cond = {
                            "cop": "<=",
                            "args": [cmd.args[0].reg_name, u],
                        }
                op = {
                    "block": "if",
                    "condition": cond,
                    "true_branch": [assign_cop(arg_to_bit(cmd.bits[0]), [1])],
                }
            case tk.ClassicalExpBox():
                exp = cmd.op.get_exp()
                match exp.op:
                    case RegWiseOp.XOR:
                        cop = "^"
                    case RegWiseOp.ADD:
                        cop = "+"
                    case RegWiseOp.SUB:
                        cop = "-"
                    case RegWiseOp.MUL:
                        cop = "*"
                    case RegWiseOp.DIV:
                        cop = "/"
                    case RegWiseOp.LSH:
                        cop = "<<"
                    case RegWiseOp.RSH:
                        cop = ">>"
                    case RegWiseOp.EQ:
                        cop = "=="
                    case RegWiseOp.NEQ:
                        cop = "!="
                    case RegWiseOp.LT:
                        cop = "<"
                    case RegWiseOp.GT:
                        cop = ">"
                    case RegWiseOp.LEQ:
                        cop = "<="
                    case RegWiseOp.GEQ:
                        cop = ">="
                    case RegWiseOp.NOT:
                        cop = "~"
                    case other:
                        logging.exception("Unsupported classical operator %s", other)
                        raise ValueError
                op = {
                    "cop": cop,
                    "args": [arg["name"] for arg in exp.to_dict()["args"]],
                }
            case m:
                raise NotImplementedError(m)
        if op:
            ops.append(op)


def genphir(
    inp: list[tuple[Ordering, ShardLayer, Cost]], *, machine_ops: bool = True
) -> str:
    """Convert a list of shards to the equivalent PHIR.

    Args:
        inp: list of shards
        machine_ops: whether to include machine ops
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
                    append_cmd(sc, ops)
            append_cmd(shard.primary_command, ops)
        if machine_ops:
            ops.append(
                {
                    "mop": "Transport",
                    "duration": (layer_cost, "ms"),
                },
            )

    # TODO(kartik): this may not always be accurate
    # https://github.com/CQCL/pytket-phir/issues/24
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
            "variable": qvar,
            "size": dim,
        }
        for qvar, dim in qvar_dim.items()
    ]

    decls += [
        {
            "data": "cvar_define",
            "data_type": "u32",
            "variable": cvar,
            "size": dim,
        }
        for cvar, dim in cvar_dim.items()
    ]

    phir["ops"] = decls + ops
    PHIRModel.model_validate(phir)
    return json.dumps(phir)
