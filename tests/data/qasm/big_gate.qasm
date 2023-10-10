OPENQASM 2.0;
include "hqslib1.inc";

creg c[1];
qreg q[4];

h q[0];
h q[1];
h q[2];

c4x q[0],q[1],q[2],q[3];

measure q[3] -> c[0];
