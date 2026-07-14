import os
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("outfile", help="Output file name")
parser.add_argument("-n", "--numlines", type=int, default=10,
                    help="Number of lines (default: 10)")

args = parser.parse_args()

# Define your bash command as a list (recommended)
command = f"grep 'memory:' {args.outfile}"

# Run the command and capture the output
result = subprocess.run(command, capture_output=True, text=True, shell=True)

# Access stdout and stderr
#print("STDOUT:\n", result.stdout)
print("STDERR:\n", result.stderr)
print("Return Code:", result.returncode)

lines=[l for l in result.stdout.split('\n') if l]

lines = sorted(lines, key=lambda x: int(x.split()[-2]) )

for line in lines[-args.numlines:]:
    print(line)