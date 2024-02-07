OPENQASM 2.0;
include "qelib1.inc";
include "hqslib1_dev.inc";

qreg q[3];
creg c[3];

ZZ q[1],q[2];

ry(0.5*pi) q[0];
ry(0.5*pi) q[2];

barrier q[0],q[1],q[2];

ry(3.5*pi) q[0];
ry(0.5*pi) q[2];


barrier q[0],q[1],q[2];
measure q[0] -> c[0];
measure q[1] -> c[1];
measure q[2] -> c[2];
