import sys
import os
import getopt
'-f file -c columes like 1,2,3 -o output'

def do():
    name = None
    url = None

    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "f:c:o:")  # 鐭€夐」妯″紡

    except:
        print("Error")

    for opt, arg in opts:
        if opt in ['-f']:
            inputfile = arg
        elif opt in ['-c']:
            columes = arg
        elif opt in ['-o']:
            outfile = arg
    awkinput = []

    for i in columes:
        print(type(i))
        if i.isdigit():
            awkinput.append('$'+str(i))
    awkinput1 = ','.join(awkinput)


    command = "awk -v OFS='\t' '{{print {2}}}' {0} > {1}".format(inputfile,outfile,awkinput1.strip(','))

    os.system(command)


do()
