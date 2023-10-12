"""NOTE: Just a placeholder to allow convenient testing of the flows."""

from pytket.circuit import Circuit
from pytket.qasm.qasm import circuit_from_qasm

from .sharding.sharder import Sharder

# Load a qasm circuit and parse
#    ,=""=,
#   c , _,{
#   /\  @ )                 __
#  /  ^~~^\          <=.,__/ '}=
# (_/ ,, ,,)          \_ _>_/~
#  ~\_(/-\)'-,_,_,_,-'(_)-(_)
circuit: Circuit = circuit_from_qasm("tests/data/qasm/baby.qasm")

# https://cqcl.github.io/tket/pytket/api/circuit_class.html

# Just a little debugging fun
print("Input circuit:")
print(circuit)
print()

sharding_output = Sharder(circuit).shard()

print("Sharding output:")
print(sharding_output)
