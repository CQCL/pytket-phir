##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from pytket.circuit import Circuit
from pytket.extensions.quantinuum.backends.api_wrappers import QuantinuumAPIOffline
from pytket.extensions.quantinuum.backends.quantinuum import (
    QuantinuumBackend,
)
from pytket.passes import DecomposeBoxes


def rebase_to_qtm_machine(circuit: Circuit, qtm_machine: str) -> Circuit:
    """Rebases a circuit's gate to the gate set appropriate for the given machine."""
    qapi_offline = QuantinuumAPIOffline()
    backend = QuantinuumBackend(
        device_name=qtm_machine,
        machine_debug=False,
        api_handler=qapi_offline,  # type: ignore [arg-type]
    )

    # Decompose boxes to ensure no problematic phase gates
    DecomposeBoxes().apply(circuit)

    # Optimization level 0 includes rebasing and little else
    # see: https://cqcl.github.io/pytket-quantinuum/api/#default-compilation
    return backend.get_compiled_circuit(circuit, 0)
