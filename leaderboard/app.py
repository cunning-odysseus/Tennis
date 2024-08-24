import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import and_, or_
import module
import re


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
    date = db.Column(db.String(80), nullable=False)
    
    
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
    date = request.form.get('date')   
    datetime_object = datetime.strptime(date, "%Y-%m-%d")
    
    if datetime_object >= datetime.now():
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
    
    # Controle of de persoon al bestaat, zo ja dan bestaat er ook al een rating voor die persoon
    # en kan daarmee gerekend worden. Zo nee, dan krijgt de speler een default rating van 400.
    if user_id_exists(player_1):
        rating_player_1 = Players.query.get(player_1).rating

    elif user_id_exists(player_1) == False:
        rating_player_1 = Players(user_id=player_1, rating=400)
        db.session.add(rating_player_1)
        db.session.commit()

    if user_id_exists(player_2):
        rating_player_2 = Players.query.get(player_2).rating

    elif user_id_exists(player_2) == False:
        rating_player_2 = Players(user_id=player_2, rating=400)
        db.session.add(rating_player_2)
        db.session.commit()
    
    # In het geval een van de beide spelers nog niet bestond moeten ze 
    # eerst opnieuw opgehaald worden, vandaar deze statement
    if bool(user_id_exists(player_1)) and bool(user_id_exists(player_2)):
        rating_player_1 = Players.query.get(player_1).rating
        rating_player_2 = Players.query.get(player_2).rating
        p1 = module.prob_win(rating_player_1, rating_player_2)
        p2 = 1 - p1 
    else:
        print('Spelers zijn niet succesvol aangemaakt')

    # Rating 
    if score_1 > score_2:
        new_rating_p1 = module.update_rating(rating_player_1, 1, p1)
        new_rating_p2 = module.update_rating(rating_player_2, 0, p2)
        Players.query.get(player_1).rating = new_rating_p1
        Players.query.get(player_2).rating = new_rating_p2
    
    elif score_1 < score_2:
        new_rating_p1 = module.update_rating(rating_player_1, 0, p1)
        new_rating_p2 = module.update_rating(rating_player_2, 1, p2)
        
        Players.query.get(player_1).rating = new_rating_p1
        Players.query.get(player_2).rating = new_rating_p2

    # Nieuwe wedstrijdgegevens naar de server sturen
    new_match = MatchHistory(player_1=player_1, player_2=player_2, score_1=score_1, score_2=score_2, date=date)
    db.session.add(new_match)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/update/<int:match_id>', methods=['GET', 'POST'])
def update_item(match_id):
    """
    Deze pagina wordt gebruikt voor het aanpassen van een bestaande uitslag. 
    """
    # Ophalen van wedstrijd die aangepast moet worden adhv match id
    match_to_update = MatchHistory.query.get(match_id)
    
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
    
    # Verrijken met nieuwe wedstrijd gegevens 
    match_to_update.player_1 = player_1
    match_to_update.player_2 = player_2
    match_to_update.score_1 = score_1
    match_to_update.score_2 = score_2
    
    # Nieuwe ratings
    rating_player_1 = Players.query.get(player_1).rating
    rating_player_2 = Players.query.get(player_2).rating
    
    p1 = module.prob_win(rating_player_1, rating_player_2)
    p2 = 1 - p1

    # TODO Hier gaat iets niet helemaal goed. Ik wil eigenlijk dat de rating van voor de wedstrijd gebruikt wordt om 
    # de nieuwe rating te berekenen bij een wijziging. Wat er nu gebeurd is dat de rating van na de wedstrijd die aangepast wordt
    # gebruikt wordt om de nieuwe rating te berekenen. Het resultaat hiervan is dat je een onjuiste rating krijgt bij het wijzigen 
    # en dat je wanneer je dezelfde uitslag houdt je toch een nieuwe rating krijgt. 
    if score_1 > score_2:
        new_rating_p1 = module.update_rating(rating_player_1, 1, p1)
        new_rating_p2 = module.update_rating(rating_player_2, 0, p2)
        
        Players.query.get(player_1).rating = new_rating_p1
        Players.query.get(player_2).rating = new_rating_p2
    
    elif score_1 < score_2:
        new_rating_p1 = module.update_rating(rating_player_1, 0, p1)
        new_rating_p2 = module.update_rating(rating_player_2, 1, p2)
        
        Players.query.get(player_1).rating = new_rating_p1
        Players.query.get(player_2).rating = new_rating_p2

    # Insturen naar de server
    db.session.add(match_to_update)    
    db.session.commit()
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
    
    
    
