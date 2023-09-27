##############################################################################
#
# (c) 2023 @ Quantinuum LLC. All Rights Reserved.
# This software and all information and expression are the property of
# Quantinuum LLC, are Quantinuum LLC Confidential & Proprietary,
# contain trade secrets and may not, in whole or in part, be licensed,
# used, duplicated, disclosed, or reproduced for any purpose without prior
# written permission of Quantinuum LLC.
#
##############################################################################

"""
NOTE: Just a placeholder to allow convenient testing of the flows
"""

from pytket.qasm import circuit_from_qasm
from pytket import Circuit

from sharding.sharder import Sharder

# Load a qasm circuit and parse
#    ,=""=,
#   c , _,{
#   /\  @ )                 __
#  /  ^~~^\          <=.,__/ '}=
# (_/ ,, ,,)          \_ _>_/~
#  ~\_(/-\)'-,_,_,_,-'(_)-(_) 
circuit: Circuit = circuit_from_qasm("tests/data/qasm/baby.qasm")

# https://cqcl.github.io/tket/pytket/api/circuit_class.html

# Just a little debuggin fun
print('Input circuit:')
print(circuit)
print()

sharding_output = Sharder(circuit).shard()