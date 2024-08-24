import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import and_, or_
import module2
import re
import pandas as pd


# Hier wordt een flask object gemaakt met de naam 'app'
app = Flask(__name__)

# Hier wordt het huidige pad opgehaald
base_dir = os.path.abspath(os.path.dirname(__file__))

# Hier wordt de string van een nieuw pad gemaakt in de huidige directory
db_dir = os.path.join(base_dir, 'data')

# Hier wordt het pad gemaakt als het nog niet bestaat
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# De app vertellen waar de database staat en wat voor database het is

# a string used to configure the connection to a database. Its typically in the format of a URL and includes the 
# username, password, hostname, database name, and port number. The format of the URL is
# dialect+driver://username:password@host:port/database.
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "match_history.db")}'

# Hier wordt de app verteld dat het niet aanpassingen moet loggen in een apart bestand
# Dat zorgt namelijk voor overhead
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Maakt integratie tussen SQLAlchemy en de app zodat je met python syntax interactie kan hebben met de app
# In simple terms, sqlalchemy() is a Python library that allows you to interact with your application’s 
# database using Python objects, rather than writing raw SQL code.
# When you use sqlalchemy() with a Flask object, it helps you to map your Python classes to the tables in 
# your database. This means you can create, read, update, and delete data in your database using Python objects, 
# without having to write SQL code.
db = SQLAlchemy(app)

# Dit is een tabel in SQLite 
class MatchHistory(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    player_1 = db.Column(db.String(80), nullable=False)
    player_2 = db.Column(db.String(80), nullable=False)
    score_1 = db.Column(db.Integer, nullable=False)
    score_2 = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    ranking_p1 = db.Column(db.Integer, nullable=True) # TODO hernoemen naar rating
    ranking_p2 = db.Column(db.Integer, nullable=True) # TODO hernoemen naar rating
    
    
class Players(db.Model):
    user_id = db.Column(db.String(80), primary_key=True)
    rating = db.Column(db.Integer, nullable=False)

# Create the database and tables within the application context
with app.app_context():
    db.create_all()
    
def user_id_exists(user_id):
    return bool(db.session.query(Players.query.filter_by(user_id=user_id).exists()).scalar())

# De route decorator wordt gebruikt om Flask te vertellen welke URL de functie zou moeten triggeren
# HTML content in de string wordt gerenderd
# @route verteld wat er moet worden laten zien wanneer je een bepaalde URL gebruikt in je browser
# Hier staat / -> dus wanneer de hoofdpagina (index page) geladen wordt, dan wordt dit laten zien   

def invullen(regelid):
    if len(request.args.keys()) == 0:
        return f'{request.url}?edit={regelid}'
    elif re.search(r"[?&]edit=", request.url):
        return re.sub(r'edit=[0-9]+', 'edit=' + str(regelid), request.url)
    else:
        return f'{request.url}&edit={regelid}'

@app.route('/', methods=['GET'])
def index():
    """
    Hiermee wordt de hoofdpagina geladen
    """
    
    conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    conn.close()
    
    match_history['date'] = pd.to_datetime(match_history['date'])
    match_history = match_history.sort_values('match_id', ascending=True)
    
    match_history['result_p1'] = match_history.apply(lambda row: module2.determine_result(row, player=1), axis=1)
    match_history['result_p2'] = match_history.apply(lambda row: module2.determine_result(row, player=2), axis=1)
    
    current_rating = {}
    for name in (list(match_history['player_1'].drop_duplicates()) + list(match_history['player_2'].drop_duplicates())):
        current_rating[name] = 400
        
    for index, row in match_history.iterrows():
        p1 = row['player_1']
        p2 = row['player_2']
        current_rating_p1 = current_rating[p1]
        current_rating_p2 = current_rating[p2]
    
        table = module2.update_rating(row['player_1'], row['player_2'], row['result_p1'], row['result_p2'], row['date'], current_rating_p1= current_rating_p1, current_rating_p2=current_rating_p2)
        current_rating[p1] = table[f'new_rating_{p1}']
        current_rating[p2] = table[f'new_ranting_{p2}']
        match_history.iloc[index, 6] = current_rating[p1]
        match_history.iloc[index, 7] = current_rating[p2]
    
    match_history = match_history.drop(columns=['result_p1', 'result_p2'])
    match_history = match_history.sort_values('date', ascending=False)

    # Write the DataFrame to the db
    conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    conn.close()
    
    
    # Hier wordt de tabel met ratings opgehaald
    player_rating = Players.query.order_by(Players.rating.desc()).all()
    # De volgende if / else zijn er om de filter op de tabel te handelen
    
    # Als er in de filter een speler en een datum wordt meegegeven wordt er een GET request gestuurd met daarin de speler en datum in de payload.
    # In de URL staat de speler en de datum en daarom wordt er hier met request.args.keys() gekeken wat dan meegestuurd is. Deze filosofie wordt ook
    # bij de gevallen van enkel speler, enkel datum of niks toegepast.
    if ('player' in request.args.keys() and bool(request.args['player'])) and ('date' in request.args.keys() and bool(request.args['date'])):
        player_name = request.args['player']
        date_search = request.args['date']
        match_history_table = MatchHistory.query.filter(
            and_
                (or_(MatchHistory.player_1 == player_name, MatchHistory.player_2 == player_name)),
                MatchHistory.date == date_search
        )
        
    elif 'player' in request.args.keys() and bool(request.args['player']):
        player_name = request.args['player']
        match_history_table = MatchHistory.query.filter(or_(MatchHistory.player_1 == player_name, MatchHistory.player_2 == player_name))
        
    elif 'date' in request.args.keys() and bool(request.args['date']):
        date_search = request.args['date']
        match_history_table = MatchHistory.query.filter(MatchHistory.date == date_search)
    
    else:      
        match_history_table = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
    
    # Deze if handeld de edit knop op de homepagina hierbij wordt op dezelfde wijze als hierboven gekeken naar wat er in de GET request wordt gestuurd
    # maar dan wordt dat hier als bepalende factor voor de pagina layout gebruikt. (of invulvelden worden geladen met save en annuleren knoppen)
    if 'edit' in request.args.keys():
        match_id = int(request.args['edit'])
        return render_template('home.html', match_history_table=match_history_table, match_id=match_id, Player_rating=player_rating, invullen=invullen)
    
    return render_template('home.html', match_history_table=match_history_table, Player_rating=player_rating, invullen=invullen)

# Deze URL kan je niet bezoeken, maar dient alleen om iets in te voeren vandaar de methode POST
@app.route('/add', methods=['POST'])
def add_match():
    """ 
    Dit is de pagina waarin een post verstuurd wordt naar de server met de wedstrijd input.
    """
    # Hier wordt de informatie opgehaald uit de velden
    player_1 = request.form.get('player_1')
    player_2 = request.form.get('player_2')
    score_1 = request.form.get('score_1')
    score_2 = request.form.get('score_2')
    date = datetime.strptime(request.form.get('datetime'), "%Y-%m-%dT%H:%M")
    # datetime_object = datetime.strptime(date, "%Y-%m-%d")
    
    if date >= datetime.now():
        return 'Mag niet in de toekomst zijn'
    
    # Controle op gelijkspel
    if score_1 == score_2:
        return 'Score mag niet gelijk zijn'
    else:
        pass

    # Controle op naam
    if player_1 or player_2 == None:
        print('Spelersnaam mag niet leeg zijn')
    else:
        pass
    
    conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    conn.close()
    
    if len(match_history['match_id']) == 0:
        new_id = 1
    else:
        new_id = int(match_history['match_id'].max() + 1)
    
    new_row = pd.DataFrame({
        'match_id': new_id,
        'player_1': player_1,
        'player_2': player_2,
        'score_1': score_1,
        'score_2': score_2,
        'date': date,
        'ranking_p1': '',
        'ranking_p2': ''
    }, index=[0])
    match_history['date'] = pd.to_datetime(match_history['date'])
    match_history = pd.concat([match_history, new_row], ignore_index=True).sort_values('date')
    
    # Apply the function row-wise
    match_history['result_p1'] = match_history.apply(lambda row: module2.determine_result(row, player=1), axis=1)
    match_history['result_p2'] = match_history.apply(lambda row: module2.determine_result(row, player=2), axis=1)
    
    current_rating = {}
    for name in (list(match_history['player_1'].drop_duplicates()) + list(match_history['player_2'].drop_duplicates())):
        current_rating[name] = 400
        
    for index, row in match_history.iterrows():
        print(index)
        p1 = row['player_1']
        p2 = row['player_2']
        current_rating_p1 = current_rating[p1]
        current_rating_p2 = current_rating[p2]
    
        table = module2.update_rating(row['player_1'], row['player_2'], row['result_p1'], row['result_p2'], row['date'], current_rating_p1= current_rating_p1, current_rating_p2=current_rating_p2)
        current_rating[p1] = table[f'new_rating_{p1}']
        current_rating[p2] = table[f'new_ranking_{p2}']
        match_history.iloc[(new_id-1), 6] = current_rating[p1]
        match_history.iloc[(new_id-1), 7] = current_rating[p2]
    
    match_history = match_history.drop(columns=['result_p1', 'result_p2'])
    match_history = match_history.sort_values('date', ascending=False)

    # Write the DataFrame to the db
    conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    conn.close()
    return redirect(url_for('index'))


@app.route('/update/<int:match_id>', methods=['POST'])
def update_item(match_id):
    """
    Deze pagina wordt gebruikt voor het aanpassen van een bestaande uitslag. 
    """
    # Ophalen van wedstrijd die aangepast moet worden adhv match id
    # match_to_update = MatchHistory.query.get(match_id)
    conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    match_to_update = pd.read_sql_query(f"SELECT * FROM match_history WHERE match_id = {match_id}", conn)
    conn.close()
    
    # Deze serie van statements checkt of er iets in de velden ingevuld is. 
    # Zo ja, wordt die waarde gebruikt. Zo nee, pakt die de oude waarde.
    if bool(request.form.get('player_1')) == True:
        player_1 = request.form.get('player_1')
    else:
        player_1 = match_to_update.player_1
    
    if bool(request.form.get('player_2')) == True:  
        player_2 = request.form.get('player_2')
    else:
        player_2 = match_to_update.player_2

    if bool(request.form.get('score_1')) == True:
        score_1 = int(request.form.get('score_1'))
    else:
        score_1 = int(match_to_update.score_1)

    if bool(request.form.get('score_2')) == True:
        score_2 = int(request.form.get('score_2'))
    else:
        score_2 = int(match_to_update.score_2)
    
    # Controlle of de scores niet gelijk zijn.
    if score_1 == score_2:
        return 'Score mag niet gelijk zijn'
    else:
        pass
    
    match_to_update['player_1'] = player_1
    match_to_update['player_2'] = player_2
    match_to_update['score_1'] = score_1
    match_to_update['score_2'] = score_2
    
    match_history = match_history.sort_values('date', ascending=False)
    # print(match_history)
    # match_history.loc[match_history['match_id'] == int(match_to_update['match_id'])] = match_to_update

    # conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    # match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    # conn.close()
    
    # conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    # match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    # conn.close()
    
    # match_history['date'] = pd.to_datetime(match_history['date'])
    # match_history = match_history.sort_values('date')
    
    # # Apply the function row-wise
    # match_history['result_p1'] = match_history.apply(lambda row: module2.determine_result(row, player=1), axis=1)
    # match_history['result_p2'] = match_history.apply(lambda row: module2.determine_result(row, player=2), axis=1)

    # current_rating = {}
    # for name in (list(match_history['player_1'].drop_duplicates()) + list(match_history['player_2'].drop_duplicates())):
    #     current_rating[name] = 400
        
    # for index, row in match_history.iterrows():
    #     p1 = row['player_1']
    #     p2 = row['player_2']
    #     current_rating_p1 = current_rating[p1]
    #     current_rating_p2 = current_rating[p2]
    
    #     table = module2.update_rating(row['player_1'], row['player_2'], row['result_p1'], row['result_p2'], row['date'], current_rating_p1= current_rating_p1, current_rating_p2=current_rating_p2)
    #     current_rating[p1] = table[f'new_rating_{p1}']
    #     current_rating[p2] = table[f'new_ranking_{p2}']
    #     match_history.iloc[int(row['match_id'])-1, 6] = current_rating[p1]
    #     match_history.iloc[(int(row['match_id'])-1), 7] = current_rating[p2]
    
    # match_history = match_history.drop(columns=['result_p1', 'result_p2'])
    
    # match_history = match_history.sort_values('date', ascending=False)
    # print(match_history)

    # # Write the DataFrame to the db
    # conn = sqlite3.connect('/Users/caioeduardo/Documents/python_project/Tennis/leaderboard/data/match_history.db')
    # match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    # conn.close()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
    
    
    
