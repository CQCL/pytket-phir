OPENQASM 2.0;
include "hqslib1.inc";

qreg q[1];
creg a[4];
creg b[4];
creg c[4];
a = 3;
b = a;
c = (a - b);
a = (a << 1);
