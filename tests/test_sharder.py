##############################################################################
#
# (c) 2023 @ Quantinuum LLC. All Rights Reserved.
# This software and all information and expression are the property of
# Quantinuum LLC, are Quantinuum LLC Confidential & Proprietary,
# contain trade secrets and may not, in whole or in part, be licensed,
# used, duplicated, disclosed, or reproduced for any purpose without prior
# written permission of Quantinuum LLC.
#
##############################################################################

from pytket.phir.sharding.sharder import Sharder

from .sample_data import QasmFiles, get_qasm_as_circuit


class TestSharder:
    def test_ctor(self) -> None:
        sharder = Sharder(get_qasm_as_circuit(QasmFiles.baby))
        assert sharder is not None

        output = sharder.shard()

        assert len(output) == 2  # noqa: PLR2004
