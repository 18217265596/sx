import os
import sys
import getopt

argv = sys.argv[1:]

try:
    opts, args = getopt.getopt(argv, "s:p:")

except:
    print("Error")

path = ""
structure = ''

for opt, arg in opts:
    if opt in ['-p']:
        path = arg
    elif opt in ['-s']:
        structure = arg

syslist = os.listdir(path)
mutlist = []
for file in syslist:
    if 'mut' in file:
        mutlist.append(file)
    else:
        pass

for file in mutlist:
    name = file + '.slurm'
    a = open(name, 'w')
    a.write('''#!/bin/bash

#SBATCH -p cpu
#SBATCH -n 40
#SBATCH --exclusive
#SBATCH -o %j.out
#SBATCH -e %j.err
#SBATCH --job-name=glyscan
#SBATCH --mail-user=sunshine.1997@sjtu.edu.cn

module purge
module load cuda/9.0.176-gcc-4.8.5
module load openmpi/3.1.5-gcc-4.8.5 

ulimit -s unlimited
ulimit -l unlimited

export PATH=$PATH:/lustre/home/acct-clswg/clswg/rosetta/main/source/bin


mpirun -np 40 cartesian_ddg.mpi.linuxgccrelease -s {} @in/1.flag -ddg:mut_file ./in/{}
'''.format(structure,file))
    a.close()
    command = 'sbatch {}'.format(name)
    os.system(command)
