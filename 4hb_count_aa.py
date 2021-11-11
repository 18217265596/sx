sequence = 'MGKFSQLVKFLQKVLELASELQGGGGKELVKVAESVLQLVSELQKASGSGLQKVSELVKALESFSELVKAGGGGKVSELVKVLESVKELVSALEG'
'sequence modified!'
acid = []
base = []
for i in range(len(sequence)-1):
    if i % 2 == 0 and i != 0 and i != 94 :
        base.append(i)
    if i %2 == 1 and i != 1 :
        acid.append(i)

print("acid",acid)
print("base",base)

mutate_acid = []
for i in acid:
    if sequence[i] in ['G','V','A','F']:
        mutate_acid.append(i)

mutate_base = []
for i in base:
    if sequence[i] in ['G','L','A']:
        mutate_base.append(i)

'''print("mutateacid",mutate_acid)
print("mutatebase",mutate_base)'''

for i in mutate_acid:
    print('''{} A PIKAA GAVF'''.format(i+1),)
for i in mutate_base:
    print('''{} A PIKAA GLA'''.format(i+1),)
packonly = []
for i in range(len(sequence)):
        if i not in mutate_acid:
            if i not in mutate_base:
                packonly.append(i+1)
                print(i+1,sequence[i])

for i in packonly:
    print(i,end =",")

t = 0
for i in acid:
    if sequence[i] == 'V':
        print(i,sequence[i])
        t += 1
print(t)

print(len(sequence))

