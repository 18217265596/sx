import os
import sys

path = os.getcwd()
syslist = os.listdir(path)
inputlist = []
for name in syslist:
    if ".pdb" in str(name):
        print(name + " is a pdb fiel, will be converted into a svg image")
        inputlist.append(name)
    else:
        #syslist.remove(name)
        print(name + " is not a pdb file,ignoring it")
print(inputlist)

os.system(pyt)

command = "obabel -ipdb {} -osvg -O {}.svg".format(, name))

for file in inputlist:
    command = "obabel -ipdb {} -osvg -O {}.svg".format(file, file))
    os.system(command)
