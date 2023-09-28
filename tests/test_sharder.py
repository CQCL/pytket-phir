##############################################################################
#
# (c) 2023 @ Quantinuum LLC. All Rights Reserved.
from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFiles, get_qasm_as_circuit


class TestSharder:
    def test_ctor(self) -> None:
        sharder = Sharder(get_qasm_as_circuit(QasmFiles.baby))
        assert sharder is not None

        output = sharder.shard()

        assert len(output) == 3
