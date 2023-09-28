OPENQASM 2.0;
include "hqslib1.inc";

qreg q[1];
creg c[2];

h q;
measure q[0]->c[0];
reset q;
if (c==1) h q;
if (c<1) h q;
if (c>1) h q;
if (c<=1) h q;
if (c>=1) h q;
if (c!=1) h q;
measure q[0]->c[0];
