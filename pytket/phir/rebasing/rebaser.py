from pytket.circuit import Circuit
from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPIOffline
from pytket.extensions.quantinuum.backends.quantinuum import (
    QuantinuumBackend,
)
from pytket.qasm.qasm import circuit_from_qasm_str, circuit_to_qasm_str


def rebase_to_qtm_machine(circuit: Circuit, qtm_machine: str) -> Circuit:
    """Rebases a circuit's gate to the gate set appropriate for the given machine."""
    qapi_offline = QuantinuumAPIOffline()
    backend = QuantinuumBackend(
        device_name=qtm_machine,
        machine_debug=False,
        api_handler=qapi_offline,  # type: ignore [arg-type]
    )
    # Optimization level 0 includes rebasing and little else
    # see: https://cqcl.github.io/pytket-quantinuum/api/#default-compilation
    compiled = backend.get_compiled_circuit(circuit, 0)

    # NOTE: Serializing and deserializing to remove global phase gates
    as_qasm_str = circuit_to_qasm_str(compiled, header="hqslib1")
    return circuit_from_qasm_str(as_qasm_str)
