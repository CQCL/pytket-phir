OPENQASM 2.0;
include "hqslib1.inc";
include "qelib1.inc";

qreg q[4];
creg c[4];

h q[0];
h q[1];
h q[2];
h q[3];
rzz(pi/8) q[0],q[1];
rzz(pi) q[2],q[3];

measure q->c;
