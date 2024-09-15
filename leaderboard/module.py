import sqlite3
import csv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

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
    
    current_rating_df = pd.DataFrame(current_rating).sort_values('Rating', ascending=False).reset_index()
    
    return current_rating_df

def player_statistics(match_history):
    player_stats = {
        'Player': [],
        'Average score': [],
        'Wins': [],
        'Losses': []
    }
    
    for player_name in (set(list(match_history['player_1']) + list(match_history['player_2']))):
        
        selection = match_history[(match_history['player_1'] == player_name) | (match_history['player_2'] == player_name)]
        
        selection['result_p1'] = selection.apply(lambda row: determine_result(row, player=1), axis=1)
        selection['result_p2'] = selection.apply(lambda row: determine_result(row, player=2), axis=1)
        selection = selection.convert_dtypes()
        selection['score_1'] = selection['score_1'].astype(int)
        selection['score_2'] = selection['score_2'].astype(int)
        selection['date'] = pd.to_datetime(selection['date'])
        
        scores = []
        wins = []
        losses = []
    
        for index, row in selection.iterrows():
        
            if player_name in row['player_1']:
                scores.append(row['score_1'])
            
            if player_name in row['player_2']:
                scores.append(row['score_2'])
                
            if player_name in row['player_1']:
                if row['result_p1'] == 1:
                    wins.append(row['result_p1'])
                else:
                    pass
                
            if player_name in row['player_2']:
                if row['result_p2'] == 1:
                    wins.append(row['result_p2'])
                else:
                    pass
                
            if player_name in row['player_1']:
                if row['result_p1'] == 0:
                    losses.append(row['result_p1'])
                else:
                    pass
                
            if player_name in row['player_2']:
                if row['result_p2'] == 0:
                    losses.append(row['result_p2'])
                else:
                    pass
        
        player_stats['Player'].append(player_name)
        player_stats['Average score'].append(round(sum(scores) / len(scores), 2))
        player_stats['Wins'].append(len(wins))
        player_stats['Losses'].append(len(losses))  
        
    player_stats_df = pd.DataFrame(player_stats).reset_index()
    
    return player_stats_df
            
# def player_rating_progression(match_history, player_name):
#     rating_history = {
#         'Player': [],
#         'Rating': [],
#         'Date': []
#     }
#     selection = match_history[(match_history['player_1'] == player_name) | (match_history['player_2'] == player_name)]
    
#     for index, row in selection.iterrows():
#         if player_name in row['player_1']:
#             rating_history['Rating'].append(row['rating_p1'])
#             rating_history['Date'].append(row['date'])
#             rating_history['Player'].append(player_name)
            
#         elif player_name in row['player_2']:
#             rating_history['Rating'].append(row['rating_p2'])
#             rating_history['Date'].append(row['date'])
#             rating_history['Player'].append(player_name)

#     rating_history_df = pd.DataFrame(rating_history).sort_values('Date').reset_index()
    
#     return rating_history_df

def player_rating_progression(match_history):
    rating_history = {
        'Player': [],
        'Rating': [],
        'Date': []
    }
    
    for player_name in (set(list(match_history['player_1']) + list(match_history['player_2']))):
        selection = match_history[(match_history['player_1'] == player_name) | (match_history['player_2'] == player_name)]
        
        for index, row in selection.iterrows():
            if player_name in row['player_1']:
                rating_history['Rating'].append(row['rating_p1'])
                rating_history['Date'].append(row['date'])
                rating_history['Player'].append(player_name)
                
            elif player_name in row['player_2']:
                rating_history['Rating'].append(row['rating_p2'])
                rating_history['Date'].append(row['date'])
                rating_history['Player'].append(player_name)

    rating_history_df = pd.DataFrame(rating_history).sort_values('Date').reset_index()
        
    return rating_history_df

def plot_rating_progression(match_history, player):
    
    rating_progression = player_rating_progression(match_history, player)
    
    sns.lineplot(x=rating_progression['Date'], y=rating_progression['Rating'])
    plt.savefig('/Users/caioeduardo/Documents/python_project/Tennis/plots/graph.png')
    
        
        