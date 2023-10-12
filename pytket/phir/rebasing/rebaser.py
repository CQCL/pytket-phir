from pytket.circuit import Circuit
from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPIOffline
from pytket.extensions.quantinuum.backends.quantinuum import (
    QuantinuumBackend,
)


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
    return backend.get_compiled_circuit(circuit, 0)
