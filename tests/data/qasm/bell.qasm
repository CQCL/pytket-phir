OPENQASM 2.0;
include "hqslib1.inc";

qreg q[2];
creg m[2];

h q[0];
CX q[0], q[1];

measure q -> m;
