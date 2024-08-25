               
def prob_win(player_1_rating, player_2_rating):
    prob_player_1_win = 1 / ( 1 + 10**((player_2_rating - player_1_rating)/400))
    
    return prob_player_1_win

def update_rating(current_rating, score, prob_win):
    """ 
    score: 1 for win, 0 for loss and 1/2 for draw
    """
    new_rating = int(current_rating + 32*(score - prob_win))
    return new_rating