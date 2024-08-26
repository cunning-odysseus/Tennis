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
        
def most_recent_rating(match_history):
    current_rating = {'Player': [],
                      'Rating': []}
    for name in (set(list(match_history['player_1']) + list(match_history['player_2']))):
        selection = match_history[(match_history['player_1'] == name) | (match_history['player_2'] == name)]
        most_recent_date = selection[selection['date'] == selection['date'].max()]
        
        if name in most_recent_date['player_1'].values:
            most_recent_rating = most_recent_date['rating_p1'].iloc[0]
        
        elif name in most_recent_date['player_2'].values:
            most_recent_rating = most_recent_date['rating_p2'].iloc[0]
        
        else:
            print('player name not found')
        
        current_rating['Player'].append(name)
        current_rating['Rating'].append(most_recent_rating)
    
    current_rating_df = pd.DataFrame(current_rating,).sort_values('Rating', ascending=False)
    
    return current_rating_df
            

        
        