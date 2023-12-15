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
from typing import TYPE_CHECKING, Any

import pytket.circuit as tk
from phir.model import PHIRModel

from .phirgen import PHIR_HEADER, append_cmd, arg_to_bit, get_decls, tket_gate_to_phir

if TYPE_CHECKING:
    import sympy

    from pytket.unit_id import UnitID

    from .machine import Machine
    from .sharding.shard import Cost, Ordering, Shard, ShardLayer

logger = logging.getLogger(__name__)


def process_sub_commands(
    sub_commands: dict["UnitID", list[tk.Command]], max_parallel_sq_gates: int
) -> dict[int, list[tk.Command]]:
    """Create parallelizable groups of sub-commands."""
    groups: dict[
        int, list[tk.Command]
    ] = {}  # be sure to order by group number into a list when returning
    qubits2groups = {}  # track the most recent group in which a qubit was used
    # group numbers for each gate are incremented by 2 so they don't overlap
    # and different gate types don't go in the same group
    # RZ gates go in %3=1 groups, R1XY gates go in %3=1 groups,
    # and all other gates will go in %3=2 groups
    rz_group_number = -3  # will be set to 0 when first RZ gate is assigned (-3 + 3 = 0)
    r1xy_group_number = (
        -2  # will be set to 1 when first R1XY gate is assigned (-2 + 3 = 1)
    )
    other_group_number = (
        -1  # will be set to 2 when first R1XY gate is assigned (-1 + 3 = 2)
    )
    num_scs_per_qubit = {}

    for qubit in sub_commands:
        num_scs_per_qubit[qubit] = len(sub_commands[qubit])
        # set every qubit's group id to be -4
        # prevents KeyError in check for group number
        # will get set to a valid group number the first time the qubit is used
        qubits2groups[qubit] = -4
    max_len = max(num_scs_per_qubit.values())

    for index in range(max_len):
        for qubit in sub_commands:
            # check to make sure you are not accessing beyond the end of the list
            if index < num_scs_per_qubit[qubit]:
                sc = sub_commands[qubit][index]
                gate = sc.op.type
                match gate:
                    case tk.OpType.Rz:
                        group_number = rz_group_number
                        valid_pll_op = True
                    case tk.OpType.PhasedX:
                        group_number = r1xy_group_number
                        valid_pll_op = True
                    case _:
                        group_number = other_group_number
                        valid_pll_op = False
                # does a group exist for that gate type?
                group_available = group_number in groups
                # is that group later in execution than the
                # most recent group for an op on that qubit?
                order_preserved = group_number > qubits2groups[qubit]
                # is the group size still under the maximum allowed parallel ops?
                group_size = len(groups[group_number]) if group_number in groups else 0
                group_not_too_large = group_size < max_parallel_sq_gates
                # is the op parallelizable (only RZ or R1XY)?
                if (
                    group_available
                    and order_preserved
                    and group_not_too_large
                    and valid_pll_op
                ):
                    groups[group_number].append(sc)
                    qubits2groups[qubit] = group_number
                else:
                    # make a new group:
                    match gate:
                        case tk.OpType.Rz:
                            rz_group_number += 3
                            group_number = rz_group_number
                        case tk.OpType.PhasedX:
                            r1xy_group_number += 3
                            group_number = r1xy_group_number
                        case _:
                            other_group_number += 3
                            group_number = other_group_number
                    groups[group_number] = [sc]
                    qubits2groups[qubit] = group_number

    return dict(sorted(groups.items()))


def groups2qops(groups: dict[int, list[tk.Command]], ops: list[dict[str, Any]]) -> None:  # noqa: PLR0912
    """Convert the groups of parallel ops to properly formatted PHIR."""
    for group in groups.values():
        angles2qops: dict[tuple[sympy.Expr | float, ...], dict[str, Any]] = {}
        for qop in group:
            if not qop.op.is_gate():
                append_cmd(qop, ops)
            else:
                angles = qop.op.params
                if tuple(angles) not in angles2qops:
                    fmt_qop: dict[str, Any] = {
                        "qop": tket_gate_to_phir[qop.op.type],
                        "angles": [angles, "pi"],
                    }
                    if len(qop.qubits) == 1:
                        fmt_qop["args"] = [arg_to_bit(qop.qubits[0])]
                    else:
                        arg = [arg_to_bit(a) for a in qop.qubits]
                        fmt_qop["args"] = [arg]
                    angles2qops[tuple(angles)] = fmt_qop
                else:
                    fmt_qop = angles2qops[tuple(angles)]
                    if len(qop.qubits) == 1:
                        fmt_qop["args"].append(arg_to_bit(qop.qubits[0]))
                    else:
                        arg = [arg_to_bit(a) for a in qop.qubits]
                        fmt_qop["args"].append(arg)
        # in the case where the qop is not a gate (a conditional for example)
        # this branch is skipped because non-gate sub-commands
        # are always the only member of their group (see process_sub_commands)
        if len(angles2qops) > 1:
            pll_block: dict[str, Any] = {"block": "qparallel", "ops": []}
            for phir_qop in angles2qops.values():
                pll_block["ops"].append(phir_qop)
            comment = {"//": f"Parallel {tket_gate_to_phir[qop.op.type]}"}
            ops.extend((comment, pll_block))
        else:
            for phir_qop in angles2qops.values():
                if len(phir_qop["args"]) > 1:
                    comment = {"//": "Parallel " + str(qop).split(" q", maxsplit=1)[0]}
                else:
                    comment = {"//": str(qop)}
                ops.extend((comment, phir_qop))


def process_shards(
    shard_layer: "ShardLayer", max_parallel_tq_gates: int, max_parallel_sq_gates: int
) -> dict[int, list["Shard"]]:
    """Break up the shard layer into parallelizable groups."""
    groups: dict[int, list[Shard]] = {}
    types2groups: dict[
        tk.OpType, int
    ] = {}  # a dict to track the last group in which a gate type was used
    group_tracker = 0
    # parallelize shards in the same layer only
    # keeps a cap on the complexity by not having to look at
    # the relative ordering of ops in the whole circuit
    # working within layers guarantees no qubit overlap
    for shard in shard_layer:
        # the gate is a quantum op with a fixed number of arguments and
        # a known machine restriction (i.e. not Barrier, TK2, etc)
        # TODO(asa): add support for barriers
        # https://github.com/CQCL/pytket-phir/issues/55
        eligible_command_type = shard.primary_command.op.type in tket_gate_to_phir
        # a group is available for that gate type
        group_available = shard.primary_command.op.type in types2groups
        # the group size does not exceed the max number of parallel gates
        args = shard.primary_command.qubits
        num_args = len(args)
        group_not_full = False
        if group_available:
            group_number = types2groups[shard.primary_command.op.type]
            group = groups[group_number]
            tq_case = (num_args == 2) and (len(group) < max_parallel_tq_gates)  # noqa: PLR2004
            sq_case = (num_args == 1) and (len(group) < max_parallel_sq_gates)
            if tq_case or sq_case:
                group_not_full = True
        # if all 3 conditions hold, add the shard to the existing group
        if eligible_command_type and group_available and group_not_full:
            group.append(shard)
            types2groups[shard.primary_command.op.type] = group_number
        else:
            # otherwise, make a new group
            groups[group_tracker] = [shard]
            types2groups[shard.primary_command.op.type] = group_tracker
            group_tracker += 1

    groups = consolidate_sub_commands(groups)
    return dict(sorted(groups.items()))


def consolidate_sub_commands(
    groups: dict[int, list["Shard"]],
) -> dict[int, list["Shard"]]:
    """Group all the sub_commands into the first shard in the group.

    This allows maximum parallelization of sub-commands across shards.
    """
    for shards in groups.values():
        # stuckee == the shard that gets 'stuck' with all the sub-commands
        stuckee = shards[0]
        # if the group of shards only contains one element, do nothing,
        # the sub-commands are already packed into one shard
        if len(shards) > 1:
            for i in range(1, len(shards)):
                working_shard = shards[i]
                stuckee.sub_commands.update(working_shard.sub_commands)
                working_shard.sub_commands.clear()
    return groups


def format_and_add_primary_commands(
    group: list["Shard"], ops: list[dict[str, Any]]
) -> None:
    """Create properly formatted PHIR for parallel primary commands."""
    if len(group) == 1:
        append_cmd(group[0].primary_command, ops)
    else:
        num_angles = len(group[0].primary_command.op.params)
        # format the ops with no angles
        if num_angles == 0:
            gate_type = tket_gate_to_phir[group[0].primary_command.op.type]
            # for init, just append normally
            if gate_type == "Init":
                for shard in group:
                    append_cmd(shard.primary_command, ops)
            # for measure, format and include "returns"
            elif gate_type == "Measure":
                fmt_measure: dict[str, Any] = {
                    "qop": "Measure",
                    "args": [],
                    "returns": [],
                }
                for shard in group:
                    pc = shard.primary_command
                    fmt_measure["args"].append(arg_to_bit(pc.args[0]))
                    fmt_measure["returns"].append(arg_to_bit(pc.bits[0]))
                ops.append(fmt_measure)
            # all other gates, treat as standard qops
            else:
                fmt_qop: dict[str, Any] = {"qop": gate_type, "args": []}
                for shard in group:
                    pc = shard.primary_command
                    fmt_qop["args"].append(arg_to_bit(pc.args[0]))
                ops.append(fmt_qop)
        else:
            fmt_g2q: dict[int, list[tk.Command]] = {0: []}
            for shard in group:
                fmt_g2q[0].append(shard.primary_command)
            groups2qops(fmt_g2q, ops)


def genphir_parallel(
    inp: list[tuple["Ordering", "ShardLayer", "Cost"]], machine: "Machine"
) -> str:
    """Convert a list of shards to the equivalent PHIR with parallel gating.

    Args:
        inp: list of shards
        machine: a QTM machine on which to simulate the circuit
    """
    max_parallel_tq_gates = len(machine.tq_options)
    max_parallel_sq_gates = len(machine.sq_options)

    phir = PHIR_HEADER
    phir["metadata"]["strict_parallelism"] = "true"
    ops: list[dict[str, Any]] = []

    qbits = set()
    cbits = set()
    for _orders, shard_layer, layer_cost in inp:
        # within each shard layer, create groups of parallelizable shards
        # squash all the sub-commands into the first shard in the group
        shard_groups = process_shards(
            shard_layer, max_parallel_tq_gates, max_parallel_sq_gates
        )
        for group in shard_groups.values():
            for shard in group:
                qbits |= shard.qubits_used
                cbits |= shard.bits_read | shard.bits_written
                if shard.sub_commands.values():
                    # sub-commands are always sq gates
                    subcmd_groups = process_sub_commands(
                        shard.sub_commands, max_parallel_sq_gates
                    )
                    groups2qops(subcmd_groups, ops)
            format_and_add_primary_commands(group, ops)

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
