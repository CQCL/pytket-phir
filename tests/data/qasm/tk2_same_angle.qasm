OPENQASM 2.0;
include "hqslib1.inc";

creg c[4];
qreg q[4];

Rxxyyzz(0.5, 0.5, 0.5) q[0],q[1];
Rxxyyzz(0.5, 0.5, 0.5) q[2],q[3];

measure q->c;
