def prob_win(player_1_rating, player_2_rating):
    prob_player_1_win = 1 / ( 1 + 10**((player_2_rating - player_1_rating)/400))
    
    return prob_player_1_win

def update_rating(current_rating, score, prob_win):
    """ 
    score: 1 for win, 0 for loss and 1/2 for draw
    """
    new_rating = current_rating + 32*(score - prob_win)
    return new_rating


p1 = prob_win(1656, 1763)
p2 = 1 - p1

update_p1 = update_rating(1656, 1, p1)
print(update_p1)

update_p2 = update_rating(1763, 0, p2)
print(update_p2)
                             

