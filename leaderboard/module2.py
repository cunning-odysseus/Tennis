import sqlite3
import csv
import pandas as pd


def prob_win(current_rating_p1, current_rating_p2,):
    prob_player_1_win = 1 / ( 1 + 10**((current_rating_p1 - current_rating_p2)/400))
    
    return prob_player_1_win

def update_rating(p1, p2, result_p1, result_p2, date, current_rating_p1=400, current_rating_p2=400):
    """ 
    score: 1 for win, 0 for loss and 1/2 for draw
    """
    result = {}
    
    p_win_p1 = prob_win(current_rating_p1, current_rating_p2)
    p_win_p2 = 1 - p_win_p1
    
    new_rating_player_1 = int(current_rating_p1 + 32*(result_p1 - p_win_p1))
    new_rating_player_2 = int(current_rating_p2 + 32*(result_p2 - p_win_p2))
    
    result[f'p_win {p1}'] = p_win_p1
    result[f'p_win {p2}'] = p_win_p2
    result[f'new_rating_{p1}'] = new_rating_player_1
    result[f'new_rating_{p2}'] = new_rating_player_2
    result['date'] = date
    return result
 
# column_names = ['match_id', 'p1', 'p2', 'score1', 'score2', 'date']
# match_history_table = pd.read_csv('/Users/caioeduardo/Documents/python_project/Tennis/output.csv', names=column_names)
# match_history_table = match_history_table.sort_values('date', ascending=True)

# for row, value in match_history_table.items():
def determine_result(row, player):
    if player == 1:
        if row['score_1'] > row['score_2']:
            return 1
        else:
            return 0
        
    if player == 2:
        if row['score_2'] > row['score_1']:
            return 1
        else:
            return 0

# # Apply the function row-wise
# match_history_table['result_p1'] = match_history_table.apply(lambda row: determine_result(row, player=1), axis=1)
# match_history_table['result_p2'] = match_history_table.apply(lambda row: determine_result(row, player=2), axis=1)


# current_rating = {}
# for name in (list(match_history_table['p1'].drop_duplicates()) + list(match_history_table['p2'].drop_duplicates())):
#     current_rating[name] = 400


# for index, row in match_history_table.iterrows():
#     p1 = row['p1']
#     p2 = row['p2']
#     current_rating_p1 = current_rating[p1]
#     current_rating_p2 = current_rating[p2]
    
#     table = update_rating(row['p1'], row['p2'], row['result_p1'], row['result_p2'], row['date'], current_rating_p1= current_rating_p1, current_rating_p2=current_rating_p2)
#     current_rating[p1] = table[f'new_rating_{p1}']
#     current_rating[p2] = table[f'new_ranking_{p2}']
    
# print(current_rating) 