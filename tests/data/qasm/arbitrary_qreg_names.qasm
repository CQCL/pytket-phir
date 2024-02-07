OPENQASM 2.0;
include "qelib1.inc";
include "hqslib1_dev.inc";

qreg q[2];
qreg a[2];
creg c[2];
creg l[2];
ry(0.5*pi) q[0];
rx(3.5*pi) q[1];
rz(3.5*pi) q[1];
ZZ q[0],q[1];
rz(3.5*pi) q[0];
ry(3.5*pi) q[1];
barrier q[0],q[1];
rz(3.5*pi) q[0];
rx(0.5*pi) q[1];
ry(0.5*pi) q[1];
ZZ q[0],q[1];
ry(3.5*pi) q[0];
rx(3.5*pi) q[1];
barrier q[0],q[1];
barrier q[0], a[0];
x a[0];
h a[0];
ZZ q[0], a[0];
barrier q[0], a[0];
ZZ q[0], a[0];
h a[0];
measure a[0] -> l[0];
measure q[0] -> c[0];
barrier q[1], a[1];
x a[1];
h a[1];
ZZ q[1], a[1];
barrier q[1], a[1];
ZZ q[1], a[1];
h a[1];
measure a[1] -> l[1];
measure q[1] -> c[1];
