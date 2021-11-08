import sys
import os
import getopt

'-f file -c columes like 1,2,3 -o output'

def do():
    name = None
    url = None

    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "f:c:o:h")

    except:
        print("Error")

    inputfile = ""
    columes = ''
    outfile = ''
    command = ''

    for opt, arg in opts:
        if opt in ['-f']:
            inputfile = arg
        elif opt in ['-c']:
            columes = arg
        elif opt in ['-o']:
            outfile = arg
        elif opt in ['-h']:
            print('''-f filename ; -c columes e.g.: -c 1,2,3 -o out ''')
    awkinput = []
    awkinput1 = ''
    if len(inputfile) == 0:
        print('plz name inputfile use -f inputfile')
    if len(columes) == 0:
        print('plz name columes to extract use -c columes in comma seperated numbers')
    if len(outfile) != 0 and len(inputfile) != 0 and len(columes) != 0:
        for i in columes:
            print(type(i))
            if i.isdigit():
                awkinput.append('$' + str(i))
        awkinput1 = ','.join(awkinput)
        command = "awk -v OFS='\t' '{{print {2}}}' {0} > {1}".format(inputfile,outfile,awkinput1.strip(','))
    elif len(inputfile) != 0 and len(columes) != 0:
        command = "awk -v OFS='\t' '{{print {2}}}' {0} > {1}".format(inputfile, 'extracted_columes', awkinput1.strip(','))
        print("no outputname specified,will output as extracted_columes")

    os.system(command)


do()

path = sys.argv[1]
syslist = os.listdir(path)
fasta_list = []
for name in syslist:
    if ".fasta" in name:
        print(name + " is a fasta file ")
        fasta_list.append(name)
    else:
        print(name + " has been ignored cus it's not a fasta file")
print(fasta_list)


for name in fasta_list:
    inputname = name.rstrip('.fasta')+".slurm"
    os.mknod(inputname)
    file = open(inputname, "w")
    file.write('''#!/bin/bash
#SBATCH --job-name={}
#SBATCH --partition=dgx2
#SBATCH -N 1
#SBATCH -x vol04,vol05
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=6
#SBATCH --gres=gpu:1          # use 1 GPU
#SBATCH --output=%j.out
#SBATCH --error=%j.err

module load alphafold

run_af2  $PWD --preset=casp14  {}  --max_template_date=2021-09-12    '''.format(name, name))
    file.close()

for name in fasta_list:
  print(name.rstrip('.fasta'))
  command = 'sbatch {}'.format(name.rstrip('.fasta')+".slurm")
  print(command)
  os.system(command)   

