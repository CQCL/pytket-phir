class Machine:
    """A machine info class for testing"""

    def __init__(  # noqa: PLR0913
        self,
        size: int,
        tq_options: set[int],
        tq_time: float,
        sq_time: float,
        qb_swap_time: float,
    ):
        self.size = size
        self.tq_options = tq_options
        self.sq_options = set()
        self.tq_time = tq_time
        self.sq_time = sq_time
        self.qb_swap_time = qb_swap_time

        for i in self.tq_options:
            self.sq_options.add(i)
            self.sq_options.add(i + 1)
