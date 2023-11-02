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
    def test_pytket_to_phir_h1_1_all_circuits(self, test_file: QasmFile) -> None:
        """Standard case."""
        circuit = get_qasm_as_circuit(test_file)

        assert pytket_to_phir(circuit, QtmMachine.H1_1)
