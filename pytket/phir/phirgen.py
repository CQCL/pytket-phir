import json
import logging
from typing import Any

from phir.model import Bit, PHIRModel
from pytket.circuit import (
    BarrierOp,
    ClassicalExpBox,
    Command,
    Conditional,
    Op,
    OpType,
    RangePredicateOp,
    SetBitsOp,
)
from pytket.unit_id import UnitID

from .sharding.shard import Cost, Layer, Ordering

logger = logging.getLogger(__name__)

tket_gate_to_phir = {
    OpType.CX:          "CX",
    OpType.CY:          "CY",
    OpType.CZ:          "CZ",
    OpType.H:           "H",
    OpType.Measure:     "Measure",
    OpType.noop:        "I",
    OpType.PhasedX:     "R1XY",
    OpType.Reset:       "Reset",  # TODO(kartik): confirm
    OpType.Rx:          "RX",
    OpType.Ry:          "RY",
    OpType.Rz:          "RZ",
    OpType.S:           "SZ",
    OpType.Sdg:         "SZdg",
    OpType.SWAP:        "SWAP",
    OpType.SX:          "SX",
    OpType.SXdg:        "SXdg",
    OpType.T:           "T",
    OpType.Tdg:         "Tdg",
    OpType.TK2:         "R2XXYYZZ",
    OpType.U1:          "RZ",
    OpType.V:           "SX",
    OpType.Vdg:         "SXdg",
    OpType.X:           "X",
    OpType.XXPhase:     "RXX",
    OpType.Y:           "Y",
    OpType.YYPhase:     "RYY",
    OpType.Z:           "Z",
    OpType.ZZMax:       "SZZ",
    OpType.ZZPhase:     "RZZ",
}  # fmt: skip


def arg_to_bit(arg: UnitID) -> Bit:
    """Convert tket arg to Bit."""
    return [arg.reg_name, arg.index[0]]


def write_subcmd(op: Op, args: list[UnitID]) -> dict[str, Any]:
    """Return PHIR dict give op and its arguments."""
    if op.is_gate():
        gate = tket_gate_to_phir[op.type]
        angles = (op.params, "pi") if op.params else None
        qop: dict[str, Any]
        match op.type:
            case OpType.Measure:
                qop = {
                    "cop": "Measure",
                    "returns": [arg_to_bit(args[1])],
                    "args": [arg_to_bit(args[0])],
                }

            case _:
                qop = {
                    "angles": angles,
                    "qop": gate,
                    "args": [arg_to_bit(qbit) for qbit in args],
                }
        return qop

    match op:
        case SetBitsOp():
            return {
                "cop": "=",
                "returns": [arg_to_bit(args[0])],
                "args": op.values,
            }

        case _:
            raise NotImplementedError


def write_cmd(cmd: Command, ops: list[dict[str, Any]]) -> None:
    """Convert and write a pytket command as a PHIR command.

    Args:
        cmd: pytket command obtained from pytket-phir
        ops: the list of ops to append to
    """
    ops.append({"//": str(cmd)})
    if cmd.op.is_gate():
        ops.append(write_subcmd(cmd.op, cmd.args))
    else:
        op: dict[str, Any] | None = None
        match cmd.op:
            case SetBitsOp():
                op = write_subcmd(cmd.op, cmd.args)

            case BarrierOp():
                # TODO(kartik): confirm with Ciaran
                logger.debug("Skipping Barrier")

            case Conditional():  # where the condition is equality check
                if cmd.op.width != 1:
                    # TODO(kartik): implement
                    op = None
                    logger.debug("NYI")
                op = {
                    "block": "if",
                    "condition": {
                        "cop": "==",
                        "args": [arg_to_bit(cmd.args[0]), cmd.op.value],
                    },
                    "true_branch": [write_subcmd(cmd.op.op, cmd.args[1:])],
                }

            case RangePredicateOp():
                # TODO(kartik): confirm
                logger.debug("Skipping RangePredicate")
            case ClassicalExpBox():
                # TODO(kartik): confirm
                logger.debug("Skipping ClassicalExpBox")
            case m:
                raise NotImplementedError(m)
        if op:
            ops.append(op)


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
