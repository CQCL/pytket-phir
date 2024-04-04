# type: ignore
# ruff: noqa
import json

from pytket.circuit import Bit, Circuit
from pytket.phir.api import pytket_to_phir

# test case conditional NOT
# c1 = Circuit()
# target_reg = c1.add_c_register(BitRegister(name="target_reg", size=2))
# control_reg = c1.add_c_register(BitRegister(name="control_reg", size=1))
# c1.add_c_not(arg_in=target_reg[0], arg_out=target_reg[1], condition=control_reg[0])
# phir = json.loads(pytket_to_phir(c1))

# #test case for classical explicit predicates
# c = Circuit(0, 4)
# c.add_c_and(1, 2, 3)
# c.add_c_not(1, 2)
# c.add_c_or(2, 1, 3)
# c.add_c_xor(1, 2, 3)
# print(c.get_commands())
# phir = json.loads(pytket_to_phir(c))

# # Test case for MultiBitOps
# c = Circuit(0, 4)
# c0 = c.add_c_register("c0", 2)
# c1 = c.add_c_register("c1", 2)
# c2 = c.add_c_register("c2", 2)
# c.add_c_and_to_registers(c0, c1, c2)
# c.add_c_or_to_registers(c0, c1, c2)
# c.add_c_xor_to_registers(c0, c1, c2)
# c.add_c_not_to_registers(c0, c1)
# # print(c.get_commands())
# phir = json.loads(pytket_to_phir(c))


# # test case for explicit modifier
# c = Circuit(0, 4)
# # exp modifier
# and_values = [bool(i) for i in [0, 0, 0, 1]]  # binary AND
# c.add_c_modifier(and_values, [1], 2)
# c.add_c_modifier(and_values, [Bit(2)], Bit(3))
# # exp predicate
# eq_pred_values = [True, False, False, True]  # test 2 bits for equality
# c.add_c_predicate(eq_pred_values, [0, 1], 2, "EQ")
# c.add_c_predicate(eq_pred_values, [Bit(1), Bit(2)], Bit(3), "EQ")
# print(c.get_commands())
# phir = json.loads(pytket_to_phir(c))
