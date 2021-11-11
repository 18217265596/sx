import sys
import os
import getopt

def do():
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "c:p:")

    except:
        print("Error")

    path = ""
    chain = ''

    for opt, arg in opts:
        if opt in ['-p']:
            path = arg
        elif opt in ['-c']:
            chain = arg
    syslist = os.listdir(path)
    pdblist = []
    for name in syslist:
        if ".pdb" in str(name):
            pdblist.append(name)

    for pdb in pdblist:
        command=('python ~/python_modules/get_fasta_modified.py {} {}'.format(path.strip('/')+'/'+pdb,chain))
        os.system(command)

do()
