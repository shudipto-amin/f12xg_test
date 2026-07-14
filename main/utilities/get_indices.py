import sys
import os
import subprocess

outfile = sys.argv[1]

search_str = 'test_vector'

comm = f"grep -A1 {search_str} {outfile}"

lines = subprocess.check_output(comm.split())
lines = lines.decode('utf-8')

to_print = ''
for line in lines.split('\n'):
    if search_str in line: 
        to_print += line.split(search_str)[-1] + ','
    elif 'Properties' in line:
        to_print += line.split('dim: (')[1].split(')')[0]
        print(to_print)
        to_print=''
