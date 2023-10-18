# mypy: disable-error-code="misc,no-any-unimported"

import json

from phir.model import (  # type: ignore [import-untyped]
    Cmd,
    DataMgmt,
    OpType,
    PHIRModel,
    QOp,
)
from pytket.circuit import Command
from pytket.phir.sharding.shard import Shard


def write_cmd(cmd: Command, ops: list[Cmd]) -> None:
    """Write a pytket command to PHIR qop.

    Args:
        cmd: pytket command obtained from pytket-phir
        ops: the list of ops to append to
    """
    gate = cmd.op.get_name().split("(", 1)[0]
    metadata, angles = (
        ({"angle_multiplier": "π"}, cmd.op.params)
        if gate != "Measure"
        else (None, None)
    )
    qop: QOp = {
        "metadata": metadata,
        "angles": angles,
        "qop": gate,
        "args": [],
    }
    for qbit in cmd.args:
        qop["args"].append([qbit.reg_name, qbit.index[0]])
    if cmd.bits:
        qop["returns"] = []
        for cbit in cmd.bits:
            qop["returns"].append([cbit.reg_name, cbit.index[0]])
    ops.extend(({"//": str(cmd)}, qop))


def genphir(inp: list[tuple[list[int], list[Shard], float]]) -> str:
    """Convert a list of shards to the equivalent PHIR.

    Args:
        inp: list of shards
    """
    phir = {
        "format": "PHIR/JSON",
        "version": "0.1.0",
        "metadata": {"source": "pytket-phir"},
    }
    ops: OpType = []

    qbits = set()
    cbits = set()
    for _orders, shard_layers, layer_costs in inp:
        for shard in shard_layers:
            qbits |= shard.qubits_used
            cbits |= shard.bits_read | shard.bits_written
            for sub_commands in shard.sub_commands.values():
                for sc in sub_commands:
                    write_cmd(sc, ops)
            write_cmd(shard.primary_command, ops)
        ops.append(
            {
                "mop": "Transport",
                "metadata": {"duration": layer_costs / 1000000},  # microseconds to secs
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

    decls: list[DataMgmt] = [
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
