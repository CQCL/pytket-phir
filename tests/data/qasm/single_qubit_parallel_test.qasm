OPENQASM 2.0;
include "qelib1.inc";
include "hqslib1_dev.inc";

qreg q[1];
creg c[1];
ry(3.5*pi) q[0];
rz(0.5*pi) q[0];
ry(3.5*pi) q[0];
barrier q[0];
ry(3.5*pi) q[0];
rz(3.5*pi) q[0];
ry(0.5*pi) q[0];
barrier q[0];
measure q[0] -> c[0];
