#!/bin/bash

set -e
shopt -s expand_aliases
source ~/.bashrc

qmolpro "$@"
watch qstat -u amin

