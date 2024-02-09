OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c[2];

rx(0.5*pi) q[0];
ry(3.5*pi) q[1];

rz(1.0*pi) q[1];

rx(0.5*pi) q[0];
ry(3.5*pi) q[1];

measure q[0] -> c[0];
measure q[1] -> c[1];
