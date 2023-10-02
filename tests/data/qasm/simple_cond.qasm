OPENQASM 2.0;
include "hqslib1.inc";

qreg q[1];
creg c[1];

h q;
measure q->c;
reset q;
if (c==1) h q;
measure q->c;
