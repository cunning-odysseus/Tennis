import sqlite3
import csv
import pandas as pd

# # Connect to the database
# conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
# cursor = conn.cursor()

# # Export the data to a CSV file
# with open('output.csv', 'w', newline='') as csvfile:
#     cursor.execute('SELECT * FROM your_table')
#     writer = csv.writer(csvfile)
#     writer.writerows(cursor.fetchall())

# Close the database connection
# conn.close()

def prob_win(current_rating_p1, current_rating_p2,):
    prob_player_1_win = 1 / ( 1 + 10**((current_rating_p1 - current_rating_p2)/400))
    
    return prob_player_1_win

def update_rating(p1, p2, score_p1, score_p2, date, current_rating_p1=400, current_rating_p2=400):
    """ 
    score: 1 for win, 0 for loss and 1/2 for draw
    """
    result = {}
    
    p_win_p1 = prob_win(current_rating_p1, current_rating_p2)
    p_win_p2 = 1 - p_win_p1
    
    new_rating_player_1 = int(current_rating_p1 + 32*(score_p1 - p_win_p1))
    new_ranking_player_2 = int(current_rating_p2 + 32*(score_p2 - p_win_p2))
    
    result[f'p_win {p1}'] = p_win_p1
    result[f'p_win {p2}'] = p_win_p2
    result[f'new_rating_{p1}'] = new_rating_player_1
    result[f'new_ranking_{p2}'] = new_ranking_player_2
    result['date'] = date
    return result

# print(update_rating('Alisha', 'Michiel',1, 0, '8/7/24'))
 
match_history_table = pd.read_csv('output.csv')
print(match_history_table)
                             