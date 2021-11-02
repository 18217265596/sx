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
        for i in columes.split(','):
            if i.isdigit():
                awkinput.append('$' + str(i))
        awkinput1 = ','.join(awkinput)
        command = "awk -v OFS='\t' '{{print {2}}}' {0} > {1}".format(inputfile,outfile,awkinput1.strip(','))
    elif len(inputfile) != 0 and len(columes) != 0:
        for i in columes.split(','):
            if i.isdigit():
                awkinput.append('$' + str(i))
        awkinput1 = ','.join(awkinput)
        command = "awk -v OFS='\t' '{{print {2}}}' {0} > {1}".format(inputfile, 'extracted_columes', awkinput1.strip(','))
        print("no outputname specified,will output as extracted_columes")

    os.system(command)


do()



