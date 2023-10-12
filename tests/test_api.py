from pytket.phir.api import pytket_to_phir

from .sample_data import QasmFiles, get_qasm_as_circuit


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        circuit = get_qasm_as_circuit(QasmFiles.baby)

        phir = pytket_to_phir(circuit)

        # TODO: Make this test more valuable once PHIR is actually returned
        print(phir)
        assert len(phir) > 0
