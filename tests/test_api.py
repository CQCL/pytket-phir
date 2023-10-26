from pytket.phir.api import pytket_to_phir
from pytket.phir.qtm_machine import QtmMachine

from .sample_data import QasmFile, get_qasm_as_circuit


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(QasmFile.baby)

        assert pytket_to_phir(circuit)

    def test_pytket_to_phir_h1_1(self) -> None:
        """Standard case."""
        circuit = get_qasm_as_circuit(QasmFile.baby)

        # TODO(neal): Make this test more valuable once PHIR is actually returned
        assert pytket_to_phir(circuit, QtmMachine.H1_1)
