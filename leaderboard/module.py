import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


##########################
## Rating               ##
##########################

def prob_win(current_rating_p1, current_rating_p2,):
    """ 
    Berekend de kans dat een speler wint van de ander.
    Is onderdeel van update_rating
    """
    prob_player_1_win = 1 / ( 1 + 10**((current_rating_p2 - current_rating_p1)/400))
    
    return prob_player_1_win

def update_rating(p1, p2, result_p1, result_p2, date, current_rating_p1=400, current_rating_p2=400):
    """ 
    Deze functie berekend de rating die een speler krijgt na de match afhangend van de rating die speler op dat moment heeft.
    Is onderdeel van calculate_ratings
    score: 1 for win, 0 for loss and 1/2 for draw
    """
    result = {}
    
    p_win_p1 = prob_win(current_rating_p1, current_rating_p2)
    p_win_p2 = 1 - p_win_p1
    
    new_rating_player_1 = int(current_rating_p1 + 32*(result_p1 - p_win_p1))
    new_rating_player_2 = int(current_rating_p2 + 32*(result_p2 - p_win_p2))
    
    if new_rating_player_1 < 100:
        new_rating_player_1 = 100
    
    if new_rating_player_2 < 100:
        new_rating_player_2 = 100
    
    result[f"p_win {p1}"] = p_win_p1
    result[f"p_win {p2}"] = p_win_p2
    result[f"new_rating_{p1}"] = new_rating_player_1
    result[f"new_rating_{p2}"] = new_rating_player_2
    result["date"] = date
    return result

def determine_result(row, player):
    """ 
    Bepaald of een speler de wedstrijd gewonnen of verloren heeft.
    Is onderdeel van calculate_ratings
    """
    if player == 1:
        if row["score_1"] > row["score_2"]:
            return 1
        else:
            return 0
        
    if player == 2:
        if row["score_2"] > row["score_1"]:
            return 1
        else:
            return 0
        
def calculate_ratings(match_history):
    """ Berekend de rating van alle spelers waarbij ook alle gespeelde wedstrijden meegenomen wordt """
    
    # kolommen toevoegen voor win/loss results voor elke speler
    # De functie determine result op elke rij toepassen zodat we weten welke speler gewonnen heeft
    # 1 is winst en 0 is verlies -> dit wordt weer gebruikt om te berekenen wat de rating van die speler wordt
    match_history["result_p1"] = match_history.apply(lambda row: determine_result(row, player=1), axis=1)
    match_history["result_p2"] = match_history.apply(lambda row: determine_result(row, player=2), axis=1)

    # Hier wordt een dictionary gemaakt waarbij alle spelers een startrating krijgen van 400.
    current_rating = {}
    for name in (set(list(match_history["player_1"]) + list(match_history["player_2"]))):
        current_rating[name] = 400

    # Calculate and update ratings
    for index, row in match_history.iterrows():
        p1, p2 = row["player_1"], row["player_2"] # Ophalen van spelernaam
        rating_p1, rating_p2 = current_rating[p1], current_rating[p2] # Huidige ratings ophalen

        # Functie toepassen op de rij om de ratings te berekenen. Deze functie geeft een dictionary terug met:
        # probability_win_p1, probability_win_p2, new_rating_player_1, new_rating_player_2 en date
        updated = update_rating(
            p1=p1, p2=p2,
            result_p1=row["result_p1"], result_p2=row["result_p2"],
            date=row["date"], current_rating_p1=rating_p1, current_rating_p2=rating_p2
        )
        # De nieuwe ratings van beide spelers in de dictionary "current_rating" updaten.
        current_rating[p1] = updated[f"new_rating_{p1}"]
        current_rating[p2] = updated[f"new_rating_{p2}"]
        
        # De nieuwe ratings van beide spelers toevoegen aan de wedstrijd gegevens
        match_history.at[index, "rating_p1"] = current_rating[p1]
        match_history.at[index, "rating_p2"] = current_rating[p2]

    return match_history.drop(columns=["result_p1", "result_p2"])  # Hier worden de kolommen waarin de 1 of 0 staat voor winst/verlies verwijderd 

        
def most_recent_rating(match_history):
    """ Deze functie haalt de meest recente rating op van een speler tbv de lijst op de home pagina """
    current_rating = {"Player": [],
                      "Rating": []}
    for name in (set(list(match_history["player_1"]) + list(match_history["player_2"]))):
        selection = match_history[(match_history["player_1"] == name) | (match_history["player_2"] == name)]
        
        # wedstrijd met hoogste (nieuwste) id
        most_recent_match = selection[selection["match_id"] == selection["match_id"].max()]
        
        if name in most_recent_match["player_1"].values:
            most_recent_rating = most_recent_match["rating_p1"].iloc[0]
        
        elif name in most_recent_match["player_2"].values:
            most_recent_rating = most_recent_match["rating_p2"].iloc[0]
        
        else:
            print("player name not found")
        
        current_rating["Player"].append(name)
        current_rating["Rating"].append(most_recent_rating)
    
    current_rating_df = pd.DataFrame(current_rating).sort_values("Rating", ascending=False).reset_index()
    
    return current_rating_df

##########################
## Speler statistieken  ##
##########################

def player_statistics(match_history):
    """ Functie die speler statistieken maakt """
    
    player_stats = {
        "Player": [],
        "Average score": [],
        "Wins": [],
        "Losses": []
    }
    
    for player_name in (set(list(match_history["player_1"]) + list(match_history["player_2"]))):
        
        selection = match_history[(match_history["player_1"] == player_name) | (match_history["player_2"] == player_name)]
        
        selection["result_p1"] = selection.apply(lambda row: determine_result(row, player=1), axis=1)
        selection["result_p2"] = selection.apply(lambda row: determine_result(row, player=2), axis=1)
        selection = selection.convert_dtypes()
        selection["score_1"] = selection["score_1"].astype(int)
        selection["score_2"] = selection["score_2"].astype(int)
        selection["date"] = pd.to_datetime(selection["date"])
        
        scores = []
        wins = []
        losses = []
    
        for index, row in selection.iterrows():
        
            if player_name in row["player_1"]:
                scores.append(row["score_1"])
            
            if player_name in row["player_2"]:
                scores.append(row["score_2"])
                
            if player_name in row["player_1"]:
                if row["result_p1"] == 1:
                    wins.append(row["result_p1"])
                else:
                    pass
                
            if player_name in row["player_2"]:
                if row["result_p2"] == 1:
                    wins.append(row["result_p2"])
                else:
                    pass
                
            if player_name in row["player_1"]:
                if row["result_p1"] == 0:
                    losses.append(row["result_p1"])
                else:
                    pass
                
            if player_name in row["player_2"]:
                if row["result_p2"] == 0:
                    losses.append(row["result_p2"])
                else:
                    pass
        
        player_stats["Player"].append(player_name)
        player_stats["Average score"].append(round(sum(scores) / len(scores), 2))
        player_stats["Wins"].append(len(wins))
        player_stats["Losses"].append(len(losses))  
        
    player_stats_df = pd.DataFrame(player_stats).reset_index()
    
    return player_stats_df

def performance_vs_others(match_history, user):
    """ Functie die een overzicht geeft van performance van de user ten opzichte van tegenstanders """
    
    # Selectie maken van de wedstrijd geschiedenis waar de current user in gespeeld heefts
    selection = match_history[(match_history["player_1"] == user) | (match_history["player_2"] == user)]
    
    # Kolommen maken
    selection["user_score"] = selection.apply(lambda row: row["score_1"] if row["player_1"] == user else row["score_2"], axis=1)
    selection["Opponent_score"] = selection.apply(lambda row: row["score_2"] if row["player_1"] == user else row["score_1"], axis=1)
    selection["Opponent"] = selection.apply(lambda row: row["player_2"] if row["player_1"] == user else row["player_1"], axis=1)

    # winst / verlies
    selection["Win"] = selection["user_score"] > selection["Opponent_score"]
    selection["Loss"] = selection["user_score"] < selection["Opponent_score"]
    selection["Win"] = selection["Win"].astype(int)
    selection["Loss"] = selection["Loss"].astype(int) 
    
    # Step 4: Group by Opponent and calculate totals
    user_performance = selection.groupby("Opponent").agg({
        "Win": "sum",
        "Loss": "sum",
        "user_score": "mean"
    }).reset_index().round(2)

    return user_performance

def player_rating_progression(match_history):
    """ Functie die de ratings van alle spelers ophaalt met de daarbij behorende datum tbv de grafiek op de statistieken pagina """

    rating_history = {
        "Player": [],
        "Rating": [],
        "Date": []
    }
    
    for player_name in (set(list(match_history["player_1"]) + list(match_history["player_2"]))):
        selection = match_history[(match_history["player_1"] == player_name) | (match_history["player_2"] == player_name)]
        
        for index, row in selection.iterrows():
            if player_name in row["player_1"]:
                rating_history["Rating"].append(row["rating_p1"])
                rating_history["Date"].append(row["date"])
                rating_history["Player"].append(player_name)
                
            elif player_name in row["player_2"]:
                rating_history["Rating"].append(row["rating_p2"])
                rating_history["Date"].append(row["date"])
                rating_history["Player"].append(player_name)

    rating_history_df = pd.DataFrame(rating_history).sort_values("Date").reset_index()
        
    return rating_history_df

def plot_rating_progression(match_history, player):
    """ Functie die de een plot maakt voor een speler en die wegschrijft"""
    
    rating_progression = player_rating_progression(match_history, player)
    
    sns.lineplot(x=rating_progression["Date"], y=rating_progression["Rating"])
    plt.savefig("/Users/caioeduardo/Documents/python_project/Tennis/plots/graph.png")
    
        