import sys
import os

sequence = sys.argv[1]

file = open('runner.py', 'r+')

lines = file.readlines()
file.close()

file_1 = open('runner.py', 'w')

lines[152] = "sequence = '''{}''' #@param {{type:'string'}}\n".format(sequence)

file_1.writelines(lines)

file_1.close()

command = 'sbatch sub.slurm'

os.system(command)
