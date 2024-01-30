OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg m[2];

h q[0];
if(m==0) barrier q[0], q[1];
CX q[0], q[1];

measure q -> m;
