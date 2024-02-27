##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json
import logging
from importlib.metadata import version
from typing import TYPE_CHECKING, Any, TypeAlias

from typing_extensions import assert_never

import pytket.circuit as tk
from phir.model import PHIRModel
from pytket.circuit.logic_exp import (
    BitLogicExp,
    BitWiseOp,
    Constant,
    LogicExp,
    RegLogicExp,
    RegWiseOp,
)
from pytket.unit_id import Bit as tkBit
from pytket.unit_id import BitRegister

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pytket.unit_id import Qubit, UnitID

    from .sharding.shard import Cost, Ordering, ShardLayer

logger = logging.getLogger(__name__)

JsonDict: TypeAlias = dict[str, Any]
PHIR_HEADER: JsonDict = {
    "format": "PHIR/JSON",
    "version": "0.1.0",
    "metadata": {"source": f'pytket-phir v{version("pytket-phir").split("+")[0]}'},
}
UINTMAX = 2**32 - 1

Var: TypeAlias = str
Bit: TypeAlias = list[Var | int]  # e.g. [c, 0] for c[0]

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


def arg_to_bit(arg: "UnitID") -> Bit:
    """Convert tket arg to Bit."""
    return [arg.reg_name, arg.index[0]]


def assign_cop(
    lhs: list[Var] | list[Bit], rhs: "Sequence[Var | int | JsonDict | Bit]"
) -> JsonDict:
    """PHIR for classical assign operation."""
    return {
        "cop": "=",
        "returns": lhs,
        "args": rhs,
    }


def classical_op(exp: LogicExp, *, bitwise: bool = False) -> JsonDict:
    """PHIR for classical register operations."""
    match exp.op:
        # Bitwise
        case RegWiseOp.AND | BitWiseOp.AND:
            cop = "&"
        case RegWiseOp.OR | BitWiseOp.OR:
            cop = "|"
        case RegWiseOp.XOR | BitWiseOp.XOR:
            cop = "^"
        case RegWiseOp.NOT | BitWiseOp.NOT:
            cop = "~"
        case RegWiseOp.LSH:
            cop = "<<"
        case RegWiseOp.RSH:
            cop = ">>"
        # Comparison
        case RegWiseOp.EQ | BitWiseOp.EQ:
            cop = "=="
        case RegWiseOp.NEQ | BitWiseOp.NEQ:
            cop = "!="
        case RegWiseOp.LT:
            cop = "<"
        case RegWiseOp.GT:
            cop = ">"
        case RegWiseOp.LEQ:
            cop = "<="
        case RegWiseOp.GEQ:
            cop = ">="
        # Arithmetic
        case RegWiseOp.ADD:
            cop = "+"
        case RegWiseOp.SUB | RegWiseOp.NEG:
            cop = "-"
        case RegWiseOp.MUL:
            cop = "*"
        case RegWiseOp.DIV:
            cop = "/"
        case RegWiseOp.POW:
            cop = "**"
        case _:
            assert_never(exp.op)

    args: list[JsonDict | Var | Constant | Bit] = []
    for arg in exp.args:
        match arg:
            case BitLogicExp():
                args.append(classical_op(arg, bitwise=True))
            case LogicExp():
                args.append(classical_op(arg))
            case BitRegister():
                if bitwise:
                    raise TypeError
                args.append(arg.name)
            case Constant():
                if bitwise and (arg < 0 or arg > 1):
                    raise ValueError
                args.append(arg)
            case tkBit():
                if bitwise:
                    args.append(arg_to_bit(arg))
                else:
                    args.append(arg.reg_name)
            case _:
                assert_never(arg)
    return {
        "cop": cop,
        "args": args,
    }


def convert_subcmd(op: tk.Op, cmd: tk.Command) -> JsonDict | None:
    """Return PHIR dict give op and its arguments."""
    if op.is_gate():
        try:
            gate = tket_gate_to_phir[op.type]
        except KeyError:
            if op.type == tk.OpType.Phase:
                # ignore global phase
                return {"mop": "Skip"}
            logging.exception("Gate %s unsupported by PHIR", op.get_name())
            raise
        angles = (op.params, "pi") if op.params else None
        qop: JsonDict
        match gate:
            case "Measure":
                qop = {
                    "qop": gate,
                    "returns": [arg_to_bit(cmd.bits[0])],
                    "args": [arg_to_bit(cmd.args[0])],
                }
            case ("CX"
                | "CY"
                | "CZ"
                | "RXX"
                | "RYY"
                | "RZZ"
                | "R2XXYYZZ"
                | "SXX"
                | "SXXdg"
                | "SYY"
                | "SYYdg"
                | "SZZ"
                | "SZZdg"
                | "SWAP"
            ):  # two-qubit gates  # fmt: skip
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

    out: JsonDict | None = None
    match op:  # non-quantum op
        case tk.BarrierOp():
            out = {"meta": "barrier", "args": [arg_to_bit(qbit) for qbit in cmd.qubits]}

        case tk.Conditional():  # where the condition is equality check
            out = {
                "block": "if",
                "condition": {
                    "cop": "==",
                    "args": [
                        arg_to_bit(cmd.args[0])
                        if op.width == 1
                        else cmd.args[0].reg_name,
                        op.value,
                    ],
                },
                "true_branch": [convert_subcmd(op.op, cmd)],
            }

        case tk.RangePredicateOp():  # where the condition is a range
            cond: JsonDict
            match op.lower, op.upper:
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
            out = {
                "block": "if",
                "condition": cond,
                "true_branch": [assign_cop([arg_to_bit(cmd.bits[0])], [1])],
            }

        case tk.ClassicalExpBox():
            exp = op.get_exp()
            match exp:
                case BitLogicExp():
                    rhs = [classical_op(exp, bitwise=True)]
                    out = assign_cop([arg_to_bit(cmd.bits[0])], rhs)
                case RegLogicExp():
                    rhs = [classical_op(exp)]
                    out = assign_cop([cmd.bits[0].reg_name], rhs)

        case tk.SetBitsOp():
            if len(cmd.bits) != len(op.values):
                logger.error("LHS and RHS lengths mismatch for classical assignment")
                raise ValueError
            out = assign_cop([arg_to_bit(bit) for bit in cmd.bits], op.values)

        case tk.CopyBitsOp():
            if len(cmd.bits) != len(cmd.args) // 2:
                logger.warning("LHS and RHS lengths mismatch for CopyBits")
            out = assign_cop(
                [arg_to_bit(bit) for bit in cmd.bits],
                [arg_to_bit(cmd.args[i]) for i in range(len(cmd.args) // 2)],
            )

        case tk.WASMOp():
            return create_wasm_op(cmd, op)

        case _:
            # TODO(kartik): NYI
            # https://github.com/CQCL/pytket-phir/issues/25
            raise NotImplementedError

    return out


def append_cmd(cmd: tk.Command, ops: list[JsonDict]) -> None:
    """Convert a pytket command to a PHIR command and append to `ops`.

    Args:
        cmd: pytket command obtained from pytket-phir
        ops: the list of ops to append to
    """
    ops.append({"//": make_comment_text(cmd, cmd.op)})
    op: JsonDict | None = convert_subcmd(cmd.op, cmd)
    if op:
        ops.append(op)


def create_wasm_op(cmd: tk.Command, wasm_op: tk.WASMOp) -> JsonDict:
    """Creates a PHIR operation for a WASM command."""
    args, returns = extract_wasm_args_and_returns(cmd, wasm_op)
    op = {
        "cop": "ffcall",
        "function": wasm_op.func_name,
        "args": args,
        "metadata": {
            "ff_object": f"WASM module uid: {wasm_op.wasm_uid}",
        },
    }
    if cmd.bits:
        op["returns"] = returns

    return op


def extract_wasm_args_and_returns(
    command: tk.Command, op: tk.WASMOp
) -> tuple[list[str], list[str]]:
    """Extract the wasm args and return values as whole register names."""
    # This slice removes the extra `_w` cregs (wires) that are not part of the
    # circuit, and the output args which are appended after the input args
    slice_index = op.num_w + sum(op.output_widths)
    only_args = command.args[:-slice_index]
    return (
        dedupe_bits_to_registers(only_args),
        dedupe_bits_to_registers(command.bits),
    )


def dedupe_bits_to_registers(bits: "Sequence[UnitID]") -> list[str]:
    """Dedupes a list of bits to their registers, keeping order intact."""
    return list(dict.fromkeys([bit.reg_name for bit in bits]))


def make_comment_text(command: tk.Command, op: tk.Op) -> str:
    """Converts a command + op to the PHIR comment spec."""
    match op:
        case tk.Conditional():
            conditional_text = str(command)
            cleaned = conditional_text[: conditional_text.find("THEN") + 4]
            return f"{cleaned} {make_comment_text(command, op.op)}"

        case tk.WASMOp():
            args, returns = extract_wasm_args_and_returns(command, op)
            return f"WASM function={op.func_name} args={args} returns={returns}"

    return str(command)


def get_decls(qbits: set["Qubit"], cbits: set[tkBit]) -> list[dict[str, str | int]]:
    """Format the qvar and cvar define PHIR elements."""
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
        if cvar != "_w"
    ]

    return decls


def genphir(
    inp: list[tuple["Ordering", "ShardLayer", "Cost"]], *, machine_ops: bool = True
) -> str:
    """Convert a list of shards to the equivalent PHIR.

    Args:
        inp: list of shards
        machine_ops: whether to include machine ops
    """
    phir = PHIR_HEADER
    ops: list[JsonDict] = []

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

    decls = get_decls(qbits, cbits)

    phir["ops"] = decls + ops
    PHIRModel.model_validate(phir)
    return json.dumps(phir)
