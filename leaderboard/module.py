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
    
    current_rating_df = pd.DataFrame(current_rating).sort_values('Rating', ascending=False).reset_index()
    
    return current_rating_df

def player_statistics(match_history, player_name):
    player_stats = {
        'Player name': [],
        'Average score': [],
        'Wins': [],
        'Losses': []
    }
    
    selection = match_history[(match_history['player_1'] == player_name) | (match_history['player_2'] == player_name)]
    
    selection['result_p1'] = selection.apply(lambda row: determine_result(row, player=1), axis=1)
    selection['result_p2'] = selection.apply(lambda row: determine_result(row, player=2), axis=1)
    
    if player_name in selection['player_1'].values:
        scores_as_p1 = selection['score_p1'].values
        
    elif player_name in selection['player_2'].values:
        scores_as_p2 = selection['score_p2'].values

    elif player_name in selection['player_1'].values:
        wins_as_p1 = selection[selection['result_p1'] == 1].sum()

    elif player_name in selection['player_2'].values:
        wins_as_p2 =selection[selection['result_p2'] == 1].sum()
        
    elif player_name in selection['player_1'].values:
        losses_as_p1 = selection[selection['result_p1'] == 0].sum()

    elif player_name in selection['player_2'].values:
        losses_as_p2 =selection[selection['result_p2'] == 0].sum()
        
    player_stats['Player name'] = player_name
    player_stats['Average score'] = (scores_as_p1 + scores_as_p2) / len((scores_as_p1 + scores_as_p2))
    player_stats['Wins'] = wins_as_p1 + wins_as_p2
    player_stats['Losses'] = losses_as_p1 + losses_as_p2
        
    return player_stats
            
def player_rating_progression(match_history, player_name):
    rating_history = {
        'Player name': [],
        'Rating': [],
        'Date': []
    }
    
    selection = match_history[(match_history['player_1'] == player_name) | (match_history['player_2'] == player_name)]
    
    for index, row in selection.iterrows():
        
        if player_name in selection['player_1'].values:
            rating_as_p1 = selection['rating_p1'].values
            date_as_p1 = selection['date'].values
            
            rating_history['Rating'] = rating_as_p1
            rating_history['Date'] = date_as_p1
            
            
            
        elif player_name in selection['player_2'].values:
            rating_as_p2 = selection['rating_p2'].values
            date_as_p2 = selection['date'].values
            
            rating_history['Rating'] = rating_as_p1
            rating_history['Date'] = date_as_p2
        
    rating_history['Player name'] = player_name
    
    rating_history_df = pd.DataFrame(rating_history).sort_values('Date').reset_index()
    
    return rating_history_df


# # Hier wordt de tabel met ratings opgehaald
# conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db') # Verbinding maken met de database
# match_history = pd.read_sql_query("SELECT * FROM match_history", conn) # Ophalen van de gegevens die in de database zitten
# conn.close() # Verbinding sluiten

# print(player_rating_progression(match_history, 'Caio'))
# print(player_statistics(match_history, 'Caio'))
        
        