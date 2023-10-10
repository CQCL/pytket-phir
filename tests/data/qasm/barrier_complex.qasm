OPENQASM 2.0;
include "hqslib1.inc";

qreg q[4];
creg c[4];

h q[0];
h q[1];
h q[2];
h q[3];
c[3] = 1;

barrier q[0], q[1], c[3];

CX q[0], q[1];

measure q[0]->c[0];

h q[2];
h q[3];
x q[3];

barrier q[2], q[3];

CX q[2], q[3];

measure q[2]->c[2];
