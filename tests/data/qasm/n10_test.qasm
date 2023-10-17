OPENQASM 2.0;
include "qelib1.inc";

creg c[12];
qreg q[12];

cx q[0],q[1];
cx q[2],q[3];
cx q[4],q[5];
cx q[5],q[7];
cx q[7],q[8];
cx q[9],q[10];

measure q->c;
