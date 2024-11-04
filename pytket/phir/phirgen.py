##############################################################################
#
# Copyright (c) 2023-2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import json
import logging
import sys
from collections import deque
from copy import deepcopy
from importlib.metadata import version
from typing import TYPE_CHECKING, Any, TypeAlias

from pytket.qasm.qasm import QASMUnsupportedError

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never

import pytket
import pytket.circuit as tk
from phir.model import PHIRModel
from pytket.circuit import ClBitVar, ClExpr, ClOp, ClRegVar
from pytket.circuit.clexpr import has_reg_output
from pytket.circuit.logic_exp import (
    BitLogicExp,
    BitWiseOp,
    Constant,
    LogicExp,
    RegLogicExp,
    RegWiseOp,
)
from pytket.unit_id import Bit as tkBit
from pytket.unit_id import BitRegister, QubitRegister

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pytket.circuit import Circuit, WiredClExpr
    from pytket.unit_id import UnitID

    from .sharding.shard import Cost, Ordering, ShardLayer

logger = logging.getLogger(__name__)

JsonDict: TypeAlias = dict[str, Any]
PHIR_HEADER: JsonDict = {
    "format": "PHIR/JSON",
    "version": "0.1.0",
    "metadata": {"source": f"pytket-phir v{version('pytket-phir').split('+')[0]}"},
}

WASM_WORDSIZE = 32
WORDSIZE = 64 if pytket.__dict__.get("bit_width_64", False) else 32
UINTMAX = 2**WORDSIZE - 1

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


def classical_op(exp: LogicExp, *, bitwise: bool = False) -> JsonDict | int:  # noqa: PLR0912, PLR0915
    """PHIR for classical register operations."""
    match exp.op:
        # Nullary
        case BitWiseOp.ZERO:
            return 0
        case BitWiseOp.ONE:
            return 1
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


def convert_gate(op: tk.Op, cmd: tk.Command) -> JsonDict | None:
    """Return PHIR dict for a tket gate op."""
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
                "args": [arg_to_bit(cmd.qubits[0])],
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


def cop_from_op_name(op_name: str) -> str:
    """Get PHIR classical op name from pytket op name."""
    match op_name:
        case "AND":
            cop = "&"
        case "OR":
            cop = "|"
        case "XOR":
            cop = "^"
        case "NOT":
            cop = "~"
        case name:
            raise NotImplementedError(name)
    return cop


def convert_classicalevalop(op: tk.ClassicalEvalOp, cmd: tk.Command) -> JsonDict | None:  # noqa: PLR0912
    """Return PHIR dict for a pytket ClassicalEvalOp."""
    # Exclude conditional bits from args
    args = cmd.args[cmd.op.width :] if isinstance(cmd.op, tk.Conditional) else cmd.args
    out: JsonDict | None = None
    match op:
        case tk.CopyBitsOp():
            if len(cmd.bits) != len(args) // 2:
                msg = "LHS and RHS lengths mismatch for CopyBits"
                raise TypeError(msg)
            out = assign_cop(
                [arg_to_bit(bit) for bit in cmd.bits],
                [arg_to_bit(args[i]) for i in range(len(args) // 2)],
            )
        case tk.SetBitsOp():
            if len(cmd.bits) != len(op.values):
                logger.error("LHS and RHS lengths mismatch for classical assignment")
                raise ValueError
            out = assign_cop(
                [arg_to_bit(bit) for bit in cmd.bits], list(map(int, op.values))
            )
        case tk.RangePredicateOp():  # where the condition is a range
            cond: JsonDict
            match op.lower, op.upper:
                case l, u if l == u:
                    cond = {
                        "cop": "==",
                        "args": [args[0].reg_name, u],
                    }
                case l, u if u == UINTMAX:
                    cond = {
                        "cop": ">=",
                        "args": [args[0].reg_name, l],
                    }
                case 0, u:
                    cond = {
                        "cop": "<=",
                        "args": [args[0].reg_name, u],
                    }
            out = {
                "block": "if",
                "condition": cond,
                "true_branch": [assign_cop([arg_to_bit(cmd.bits[0])], [1])],
            }
        case tk.MultiBitOp():
            if len(args) % len(cmd.bits) != 0:
                msg = "Input bit- and output bit lengths mismatch."
                raise TypeError(msg)

            cop = cop_from_op_name(op.basic_op.get_name())
            is_explicit = op.basic_op.type == tk.OpType.ExplicitPredicate

            # determine number of register operands involved in the operation
            operand_count = len(args) // len(cmd.bits) - is_explicit

            iters = [iter(args)] * (operand_count + is_explicit)
            iter2 = deepcopy(iters)

            # Columns of expressions, e.g.,
            #   AND (*2) a[0], b[0], c[0]
            #          , a[1], b[1], c[1]
            #   would be [(a[0], a[1]), (b[0], b[1]), (c[0], c[1])]
            # and AND (*2) a[0], a[1], b[0]
            #            , b[1], c[0], c[1]
            #   would be [(a[0], b[1]), (a[1], c[0]), (b[0], c[1])]
            cols = zip(*zip(*iters, strict=True), strict=True)

            if all(
                all(col[0].reg_name == bit.reg_name for bit in col) for col in cols
            ):  # expression can be applied register-wise
                out = assign_cop(
                    [cmd.bits[0].reg_name],
                    [
                        {
                            "cop": cop,
                            "args": [arg.reg_name for arg in args[:operand_count]],
                        }
                    ],
                )
            else:  # apply a sequence of bit-wise ops
                exps = zip(*iter2, strict=True)
                out = {
                    "block": "sequence",
                    "ops": [
                        assign_cop(
                            [arg_to_bit(bit)],
                            [
                                {
                                    "cop": cop,
                                    "args": [
                                        arg_to_bit(arg) for arg in exp[:operand_count]
                                    ],
                                }
                            ],
                        )
                        for bit, exp in zip(cmd.bits, exps, strict=True)
                    ],
                }
        case _:
            raise NotImplementedError(op)

    return out


def multi_bit_condition(args: "list[UnitID]", value: int) -> JsonDict:
    """Construct bitwise condition."""
    min_args = 2
    if len(args) < min_args:
        msg = f"multi_bit_condition requires at least {min_args} arguments"
        raise TypeError(msg)

    def nested_cop(cop: str, args: "deque[UnitID]", val_bits: deque[int]) -> JsonDict:
        if len(args) == min_args:
            return {
                "cop": cop,
                "args": [
                    {"cop": "==", "args": [arg_to_bit(args.popleft()), val_bits.pop()]},
                    {"cop": "==", "args": [arg_to_bit(args.popleft()), val_bits.pop()]},
                ],
            }
        return {
            "cop": cop,
            "args": [
                {"cop": "==", "args": [arg_to_bit(args.popleft()), val_bits.pop()]},
                nested_cop(cop, args, val_bits),
            ],
        }

    return nested_cop("&", deque(args), deque(map(int, f"{value:0{len(args)}b}")))


def get_cop_from_op(op: ClOp) -> str | int:  # noqa: PLR0912
    """Get PHIR classical op name from ClOp."""
    cop: str | int
    match op:
        case ClOp.BitZero | ClOp.RegZero:
            cop = 0
        case ClOp.BitOne:
            cop = 1
        case ClOp.RegOne:
            cop = -1
        case ClOp.BitAnd | ClOp.RegAnd:
            cop = "&"
        case ClOp.BitOr | ClOp.RegOr:
            cop = "|"
        case ClOp.BitXor | ClOp.RegXor:
            cop = "^"
        case ClOp.BitNot | ClOp.RegNot:
            cop = "~"
        case ClOp.RegLsh:
            cop = "<<"
        case ClOp.RegRsh:
            cop = ">>"
        case ClOp.BitEq | ClOp.RegEq:
            cop = "=="
        case ClOp.BitNeq | ClOp.RegNeq:
            cop = "!="
        case ClOp.RegLt:
            cop = "<"
        case ClOp.RegGt:
            cop = ">"
        case ClOp.RegLeq:
            cop = "<="
        case ClOp.RegGeq:
            cop = ">="
        case ClOp.RegAdd:
            cop = "+"
        case ClOp.RegSub:
            cop = "-"
        case ClOp.RegMul:
            cop = "*"
        case ClOp.RegDiv:
            cop = "/"
        case ClOp.RegPow:
            cop = "**"
        case _:
            logging.exception("Classical operation %s unsupported by PHIR", str(op))
            raise NotImplementedError(op)
    return cop


def phir_from_clexpr_arg(
    expr_arg: int | ClBitVar | ClRegVar | ClExpr,
    bit_posn: dict[int, int],
    reg_posn: dict[int, list[int]],
    bits: list[tkBit],
) -> int | str | list[str | int] | JsonDict:
    """Return PHIR dict for a ClExpr."""
    match expr_arg:
        case int():
            return expr_arg
        case ClBitVar():
            bit: tkBit = bits[bit_posn[expr_arg.index]]
            return arg_to_bit(bit)
        case ClRegVar():
            bits_in_reg = [bits[i] for i in reg_posn[expr_arg.index]]
            reg_size = len(bits_in_reg)
            if reg_size == 0:
                logging.exception("Register variable with no bits")
            reg_name = bits_in_reg[0].reg_name
            if any(bit.reg_name != reg_name for bit in bits_in_reg) or any(
                bit.index[0] != i for i, bit in enumerate(bits_in_reg)
            ):
                logging.exception("Register variable not aligned with any register")
            return reg_name
    assert isinstance(expr_arg, ClExpr)  # noqa: S101

    cop = get_cop_from_op(expr_arg.op)
    if isinstance(cop, int):
        return cop
    args = [
        phir_from_clexpr_arg(arg, bit_posn, reg_posn, bits) for arg in expr_arg.args
    ]
    return {"cop": cop, "args": args}


def convert_subcmd(op: tk.Op, cmd: tk.Command) -> JsonDict | None:  # noqa: PLR0912
    """Return PHIR dict given a tket op and its arguments."""
    if op.is_gate():
        return convert_gate(op, cmd)

    out: JsonDict | None = None
    rhs: list[int | str | list[str | int] | JsonDict] = []
    match op:  # non-quantum op
        case tk.Conditional():
            out = {
                "block": "if",
                "condition": {"cop": "==", "args": [arg_to_bit(cmd.args[0]), op.value]}
                if op.width == 1
                else multi_bit_condition(cmd.args[: op.width], op.value),
                "true_branch": [convert_subcmd(op.op, cmd)],
            }

        case tk.BarrierOp():
            if op.data:
                # See https://github.com/CQCL/tket/blob/0ec603986821d994caa3a0fb9c4640e5bc6c0a24/pytket/pytket/qasm/qasm.py#L419-L459
                match op.data[0:5]:
                    case "sleep":
                        duration = op.data.removeprefix("sleep(").removesuffix(")")
                        out = {
                            "mop": "Idle",
                            "args": [arg_to_bit(qbit) for qbit in cmd.qubits],
                            "duration": (float(duration), "s"),
                        }
                    case "order" | "group":
                        raise NotImplementedError(op.data)
                    case _:
                        raise TypeError(op.data)
            else:
                out = {
                    "meta": "barrier",
                    "args": [arg_to_bit(qbit) for qbit in cmd.qubits],
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

        case tk.ClExprOp():
            wexpr: WiredClExpr = op.expr
            expr: ClExpr = wexpr.expr
            bit_posn: dict[int, int] = wexpr.bit_posn
            reg_posn: dict[int, list[int]] = wexpr.reg_posn
            output_posn: list[int] = wexpr.output_posn
            cmd_args: list[tkBit] = cmd.bits

            # TODO(AE): Check that all ClExprOps in the circuit are register-aligned
            # (i.e. that each register variable, and the register output if applicable,
            # comprises bits that constitute a complete register in the correct order).
            # https://github.com/CQCL/tket/issues/1644

            rhs = [phir_from_clexpr_arg(expr, bit_posn, reg_posn, cmd_args)]
            if has_reg_output(expr.op):
                return assign_cop([cmd_args[output_posn[0]].reg_name], rhs)
            return assign_cop([arg_to_bit(cmd_args[output_posn[0]])], rhs)

        case tk.ClassicalEvalOp():
            return convert_classicalevalop(op, cmd)

        case tk.WASMOp():
            return create_wasm_op(cmd, op)

        case _:
            # Exclude conditional bits from args
            args = (
                cmd.args[cmd.op.width :]
                if isinstance(cmd.op, tk.Conditional)
                else cmd.args
            )
            match op.type:
                case tk.OpType.ExplicitPredicate | tk.OpType.ExplicitModifier:
                    # exclude output bit when not modifying in place
                    args = args[:-1] if op.type == tk.OpType.ExplicitPredicate else args
                    out = assign_cop(
                        [arg_to_bit(cmd.bits[0])],
                        [
                            {
                                "cop": cop_from_op_name(op.get_name()),
                                "args": [arg_to_bit(arg) for arg in args],
                            }
                        ],
                    )
                case _:
                    raise NotImplementedError(op.type)

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
    # circuit and the output args, which are appended after the input args
    slice_index = op.num_w + sum(op.output_widths)
    only_args = command.args[:-slice_index]
    # Eliminate conditional bits from the front of the args
    input_args = only_args[len(only_args) - op.n_inputs :]
    if any(arg.index[0] >= WASM_WORDSIZE for arg in input_args):
        msg = "WASM support is limited to at most 32-bit registers"
        raise QASMUnsupportedError(msg)
    return (
        dedupe_bits_to_registers(input_args),
        dedupe_bits_to_registers(command.bits),
    )


def dedupe_bits_to_registers(bits: "Sequence[UnitID]") -> list[str]:
    """Dedupes a list of bits to their registers, keeping order intact."""
    return list(dict.fromkeys([bit.reg_name for bit in bits]))


def make_comment_text(cmd: tk.Command, op: tk.Op) -> str:
    """Converts a command + op to the PHIR comment spec."""
    comment = str(cmd)
    match op:
        case tk.Conditional():
            conditional_text = str(cmd)
            cleaned = (
                conditional_text[: conditional_text.find("THEN") + 5]
                if isinstance(op.op, tk.WASMOp)
                else ""
            )
            comment = f"{cleaned}{make_comment_text(cmd, op.op)}"

        case tk.WASMOp():
            args, returns = extract_wasm_args_and_returns(cmd, op)
            comment = f"WASM_function='{op.func_name}' args={args} returns={returns};"

        case tk.BarrierOp():
            comment = op.data + " " + str(cmd.args[0]) + ";" if op.data else str(cmd)

        case tk.ClassicalExpBox():
            exp = op.get_exp()
            match exp:
                case BitLogicExp():
                    comment = str(cmd.bits[0]) + " = " + str(op.get_exp())
                case RegLogicExp():
                    comment = str(cmd.bits[0].reg_name) + " = " + str(op.get_exp())

        case tk.ClExprOp():
            comment = (
                str(cmd).split(";")[0] + " of the form " + str(op.expr).split(" [")[0]
            )

    return comment


def get_decls(
    qregs: list[QubitRegister], cregs: list[BitRegister]
) -> list[dict[str, str | int]]:
    """Get PHIR declarations for qubits and classical variables."""
    decls: list[dict[str, str | int]] = [
        {
            "data": "qvar_define",
            "data_type": "qubits",
            "variable": qreg.name,
            "size": qreg.size,
        }
        for qreg in qregs
    ]

    decls += [
        {
            "data": "cvar_define",
            "data_type": f"i{WORDSIZE}",
            "variable": creg.name,
            "size": creg.size,
        }
        for creg in cregs
        if creg.name != "_w"
    ]

    return decls


def genphir(
    inp: list[tuple["Ordering", "ShardLayer", "Cost"]],
    circuit: "Circuit",
    *,
    machine_ops: bool = True,
) -> str:
    """Convert a list of shards to the equivalent PHIR.

    Args:
        inp: list of shards
        circuit: corresponding tket Circuit
        machine_ops: whether to include machine ops
    """
    phir = PHIR_HEADER
    ops: list[JsonDict] = []

    for _orders, shard_layer, layer_cost in inp:
        for shard in shard_layer:
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

    decls = get_decls(circuit.q_registers, circuit.c_registers)

    phir["ops"] = decls + ops
    PHIRModel.model_validate(phir)
    return json.dumps(phir)
