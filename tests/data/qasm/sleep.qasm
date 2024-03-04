OPENQASM 2.0;
include "hqslib1_dev.inc";

qreg q[1];
creg c[1];

rx(pi/2) q[0];

barrier q[0];
sleep(1) q[0];
barrier q[0];

rx(-pi/2) q[0];

barrier q[0];

measure q -> c;
