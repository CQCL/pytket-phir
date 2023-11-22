##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

import logging

import pytest

from pytket.phir.api import pytket_to_phir
from pytket.phir.qtm_machine import QtmMachine

from .sample_data import QasmFile, get_qasm_as_circuit

logger = logging.getLogger(__name__)


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(QasmFile.baby)

        assert pytket_to_phir(circuit)

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_no_machine_all(self, test_file: QasmFile) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(test_file)

        match test_file:
            case QasmFile.big_gate:
                with pytest.raises(KeyError, match=r".*CnX.*"):
                    assert pytket_to_phir(circuit)
            case QasmFile.qv20_0:
                with pytest.raises(KeyError, match=r".*U3.*"):
                    assert pytket_to_phir(circuit)
            case _:
                assert pytket_to_phir(circuit)

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_h1_1_all(self, test_file: QasmFile) -> None:
        """Standard case."""
        circuit = get_qasm_as_circuit(test_file)

        assert pytket_to_phir(circuit, QtmMachine.H1_1)
