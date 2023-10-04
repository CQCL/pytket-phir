OPENQASM 2.0;
include "hqslib1_dev.inc";
qreg q[1];
creg a[10];
creg b[10];
creg c[4];

// classical assignment of registers
a[0] = 1;
a = 3;
// classical bitwise functions
a = 1;
b = 3;
c = a ^ b; // XOR
// evaluating a beyond creg == int
a = 1;
b = 2;
if(a[0]==1) x q[0];
if(a!=1) x q[0];
if(a>1) x q[0];
if(a<1) x q[0];
if(a>=1) x q[0];
if(a<=1) x q[0];
if (a==10) b=1;
measure q[0] -> c[0];
