import csv
import pandas as pd
import sys
import numpy as np
import getopt
import seaborn

'-f file -c columes like 1,2,3 -o output'

def do():
    argv = sys.argv[1:]

    try:
        opts, args = getopt.getopt(argv, "f:h")

    except:
        print("Error")


    filename = ''


    for opt, arg in opts:
        if opt in ['-f']:
            filename = arg
        elif opt in ['-h']:
            print('''-f filename ''')

    df = pd.read_csv(filename,usecols=['case_name','total_score','scored_state','score_function_name'])
    df_selected = df.loc[df['scored_state'].isin(['ddG'])]
    reslist = []
    ddglist = []

    resnumbers = ['271','285','309','311','325','349','351','365','391','392','393','394','408','448','434']
    '''resnumbers = ['271', '285','309','325','349','394','448','434']'''
    residue_codes = ['A', 'R', 'N', 'D', 'C', 'Q', 'E', 'G', 'H', 'I', 'L', 'K', 'M', 'F', 'P', 'S', 'T', 'W', 'Y','V']
    list = []
    for i in range(len(resnumbers)):
        list.append([])

    for resnumber in resnumbers:
        for residue in residue_codes:
            case_name = 'complex_to_do_A{}_{}'.format(resnumber,residue)
            df_certain_residue = df_selected.loc[df_selected['case_name'].isin([case_name])]
            df_describe = df_certain_residue.describe()
            '''reslist.append('A271'+residue)'''
            list[resnumbers.index(resnumber)].append(df_describe.loc['mean', 'total_score'])

    input_array = np.array([list[i] for i in range(len(list))])
    input_df = pd.DataFrame(input_array)
    input_df.to_csv('out.csv')



    '''df_out=pd.DataFrame([resarray,ddgarray])
    df_out.to_csv('out.csv')'''



do()
