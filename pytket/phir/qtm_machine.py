from enum import Enum

from pytket.phir.machine import Machine


class QtmMachine(Enum):
    """Available machine architectures."""

    H1_1 = "H1-1"
    H1_2 = "H1-2"
    H2_1 = "H2-1"


QTM_MACHINES_MAP = {
    QtmMachine.H1_1: Machine(
        size=20,
        tq_options={0, 2, 4, 6, 8, 10, 12, 14, 16, 18},
        # need to get better timing values for below
        # but will have to look them up in hqcompiler
        tq_time=3.0,
        sq_time=1.0,
        qb_swap_time=2.0,
    ),
}
