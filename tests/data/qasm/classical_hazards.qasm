OPENQASM 2.0;
include "hqslib1.inc";

qreg q[2];
creg c[3];

h q[0];

measure q[0]->c[0];

if(c[0]==1) c[1]=1; // RAW

c[0]=0; // WAR

h q[1];

measure q[1]->c[2];

if(c[2]==1) c[0]=1; // WAW
