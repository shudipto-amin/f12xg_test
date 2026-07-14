#!/bin/bash

echo "SUMMARY of $1"
echo "============="

echo "INPUT SCRIPT"
echo "================================"
awk '
/^ Variables initialized/ { buf = ORS; next }
/^ Commands initialized/ { print buf; exit }
{ buf = buf $0 ORS }
' $1

echo "Energy outputs"
echo "==============================="
awk '
/========/ { buf = ORS; next }
/!MP2-F12/ { print buf $0 ORS; exit }
{ buf = buf $0 ORS }
' $1

