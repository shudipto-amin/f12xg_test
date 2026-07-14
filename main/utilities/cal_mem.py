import os
import sys

outfiles = sys.argv[1:]

def print_mem_stats(outfile):
    with open(outfile, 'r') as inp:
        max_words_of_mem = 0
        ntotal_ao = 'NOT FOUND'
        print(outfile)

        for n, line in enumerate(inp):
            if line.startswith(' Memory per process:'):
                print(line.rstrip('\n'))
            if line.startswith(' Total memory per node:'):
                print(line.rstrip('\n'))
            if line.startswith(' DEBUG: ntotal_ao'):
                ntotal_ao = int(line.split('=')[1].rstrip('\n'))
            if 'words of memory' in line:
                words_of_mem = line.split(' words of memory')[0]
                words_of_mem = int(words_of_mem.split()[-1])
                max_words_of_mem = max(words_of_mem, max_words_of_mem)
        
        print(f" ntotal_ao = {ntotal_ao}\n max_words_of_mem = {max_words_of_mem}")

for outfile in outfiles:
    print_mem_stats(outfile)
