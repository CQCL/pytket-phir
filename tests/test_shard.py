EMPTY_INT_SET: set[int] = set()


class TestShard:
    pass
    # def test_shard_ctor(self) -> None:
    #     circ = Circuit(4)  # qubits are numbered 0-3
    #     circ.X(0)  # first apply an X gate to qubit 0
    #     circ.CX(1, 3)  # and apply a CX gate with control qubit 1 and target qubit 3
    #     circ.Z(3)  # then apply a Z gate to qubit 3
    #     commands = circ.get_commands()

    #     shard = Shard(
    #         commands[1],
    #         {commands[0].qubits[0]: [commands[0]]},
    #         EMPTY_INT_SET,
    #     )

    #     assert shard.primary_command == commands[1]
    #     assert shard.depends_upon == EMPTY_INT_SET
    #     sub_command_key, sub_command_value = next(iter(shard.sub_commands.items()))
    #     assert sub_command_key == commands[0].qubits[0]
    #     assert sub_command_value[0] == commands[0]

    # def test_shard_ctor_conditional(self) -> None:
    #     circuit = Circuit(4, 4)
    #     circuit.H(0)
    #     circuit.Measure(0, 0)
    #     circuit.X(1, condition_bits=[0], condition_value=1)  # type: ignore [misc]
    #     circuit.Measure(1, 1)  # The command we'll build the shard from
    #     commands = circuit.get_commands()

    #     shard = Shard(
    #         commands[3],
    #         {
    #             circuit.qubits[0]: [commands[2]],
    #         },
    #         EMPTY_INT_SET,
    #     )

    #     assert len(shard.sub_commands.items())
    #     assert shard.qubits_used == {circuit.qubits[1]}
    #     assert shard.bits_read == {circuit.bits[0]}
    #     assert shard.bits_written == {circuit.bits[1]}
