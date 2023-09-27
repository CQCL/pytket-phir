OPENQASM 2.0;
include "hqslib1.inc";

qreg q[2];
creg c[2];

h q[0];
h q[1];
CX q[0], q[1];

measure q->c;
