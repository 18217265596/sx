import sys
import os

sequence = 'TFVALYDYESRTETDLSFKKGERLQIVNNTEGDWWLAHSLTTGQTGYIPSNYVAPSAPPLPPRNRPRL'
for i in range(len(sequence)):
    filename = str(i+1) + sequence[i]
    a = open(filename, 'w')
    a.writelines(('''total 1 
1       
{} {} G  ''').format(sequence[i],i+1))
    a.close()
