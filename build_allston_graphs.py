import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

#Example dictionary:
"""
allstonDictionary = {"conflict_score": 100, 
                     "transport_days": {"M": {"0": 3198, "1": 515, "2": 24}, 
                                        "T": {"0": 3092, "1": 616, "2": 29}, 
                                        "W": {"0": 3199, "1": 515, "2": 23}, 
                                        "Th": {"0": 3086, "1": 621, "2": 30}, 
                                        "F": {"0": 3666, "1": 71, "2": 0}, 
                                        "Sa": {"0": 3737, "1": 0, "2": 0}, 
                                        "Su": {"0": 3737, "1": 0, "2": 0}}, 
                 "transport_weeks": {"0": 2758, "1": 22, "2": 623, "3": 76, 
                                     "4": 240, "5": 14, "6": 4, "7": 0}, 
                 "total_round_trips": 2550, 
                 "no_lunch": {"0": 2361, "1": 253, "2": 363, "3": 126, 
                              "4": 524, "5": 110, "6": 0, "7": 0}, 
                 "no_lunch_allston": {"0": 770, "1": 53, "2": 98, "3": 16, 
                                      "4": 38, "5": 4, "6": 0, "7": 0}}

"""


def create_graphs(dictionary, filename='Schedule_Analysis_Graphs.pdf'):
    """
    Given a dictionary. Plot a graph based on key/value pairs of the nested dictinary 
    :Param dictionary: A nested dictionary that has the following keys - conflict_score,
    transport_days, transport_weeks, total_round_trips, no_lunch, no_lunch_allston
    """

    pp = PdfPages(filename)


    def lunch_graph(key, xlabel,drop0 = False):
        no_lunch = list(dictionary[key].values())[(1 if drop0 else 0):6]
        df = pd.DataFrame(no_lunch)
        if drop0:
            rename = {0:"1 day", 1:"2 days", 2:"3 days", 3:"4 days", 4:"5 days",}
        else:
            rename = {0:"0 days", 1:"1 day", 2:"2 days", 3:"3 days", 4:"4 days", 5:"5 days",}

        
        df = df.rename(rename, axis='index' )
        ax = df.plot.bar(rot=0, figsize=(8,8), fontsize=10, legend=False)
        ax.set_xlabel(xlabel, fontsize=12, labelpad=10)
        ax.set_ylabel('Number of Students', fontsize=12, labelpad=10)
        for p in ax.patches:
            ax.annotate(str(p.get_height()), (p.get_x(), p.get_height()), ha='left',
                        textcoords='offset points', xytext=(0,4), fontsize=10)
        #print(df)
        ax = plt.savefig(pp, format='pdf')

    
    #print conflict score to pdf
    # conflict_score = list(dictionary.values())[0]
    # txt = "Conflict Score: " + str(conflict_score)
    # ax = plt.figure(figsize=(15,10))
    # ax.clf()
    # ax.text(0.5, 0.5, txt, transform=ax.transFigure, size=50, ha="center")
    # ax = plt.savefig(pp, format='pdf')

    
    
    #graph transport days
    transport_days = dictionary['transport_days']
    days = list(transport_days.keys())[:5]
    df = pd.DataFrame({#"No roundtrips":[transport_days[k][0] for k in days],
                       "One roundtrip":[transport_days[k][1] for k in days],
                       "Two roundtrips":[transport_days[k][2] for k in days],},
                      index = days)
    ax = df.plot.bar(rot=0, figsize=(18,11), width=0.9, fontsize=20,)
    ax.set_xlabel('Days of the Week', fontsize=18, labelpad=10)
    ax.set_ylabel('Number of Students', fontsize=18, labelpad=10)
    ax.set_title('Round Trips to Allston, by Day', fontsize=20)
    for p in ax.patches:
        ax.annotate(str(p.get_height()), (p.get_x(), p.get_height()), ha='left',
                    textcoords='offset points', xytext=(0,4), fontsize=20)
    ax = plt.savefig(pp, format='pdf')
    
    
    #round trips
    transport_weeks = dictionary['transport_weeks']
    df = pd.DataFrame(list(transport_weeks.values())[1:],
                      index=list(transport_weeks.keys())[1:])
    ax = df.plot.bar(rot=0, figsize=(10,8), fontsize=18, legend=False )
    ax.set_xlabel('Rounds Trips per Week', fontsize=18, labelpad=10)
    ax.set_ylabel('Number of Students', fontsize=18, labelpad=10)
    ax.set_title('Round Trips to Allston, Per Week', fontsize=20)
    for p in ax.patches:
        ax.annotate(str(p.get_height()), (p.get_x(), p.get_height()), ha='left',
                    textcoords='offset points', xytext=(0,4), fontsize=20)
    ax = plt.savefig(pp, format='pdf')
    
    #no lunch allston
    lunch_graph('no_lunch', xlabel='Students without time for lunch, per week')

    #no lunch allston
    lunch_graph('no_lunch_allston_students', xlabel='Students without time for lunch, per week (at least one Allston course)')


    #no lunch allston
    lunch_graph('no_lunch_due_to_allston', xlabel='Students without time for lunch, per week (due to Allston courses)', drop0=True)
     
    pp.close()
    