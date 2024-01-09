OPENQASM 2.0;
include "qelib1.inc";

qreg q[1];
creg m[1];

rz(pi/2) q;
rx(-pi/2) q;

rx(pi/2) q;
rz(-pi/2) q;

measure q -> m;
