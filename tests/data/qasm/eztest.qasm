OPENQASM 2.0;
include "hqslib1.inc";

qreg q[3];
creg c[3];

CX q[0], q[2];
h q[0];
h q[1];
h q[2];


measure q->c;
