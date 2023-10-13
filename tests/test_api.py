from pytket.phir.api import pytket_to_phir
from pytket.phir.qtm_machine import QtmMachine

from .sample_data import QasmFiles, get_qasm_as_circuit


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.baby)

        phir = pytket_to_phir(circuit)

        # TODO: Make this test more valuable once PHIR is actually returned
        assert len(phir) > 0

    def test_pytket_to_phir_h1_1(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.baby)

        phir = pytket_to_phir(circuit, QtmMachine.H1_1)

        # TODO: Make this test more valuable once PHIR is actually returned
        assert len(phir) > 0
