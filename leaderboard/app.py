import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import module

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
    date = db.Column(db.DateTime, default=datetime.now)
    
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
@app.route('/')
def index():
    """ 
    Dit is de hoofdpagina van de website.
    Hier worden de tabellen met de uitslagen en ratings geladen, maar ook een form waarin wedstrijden
    toegevoegd kunnen worden.
    """
    match_history_table = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
    player_rating = Players.query.order_by(Players.rating.desc()).all()
    return render_template('match_history.html', match_history_table=match_history_table, Player_rating=player_rating)

@app.route('/<int:match_id>')
def index_id(match_id):
    """ 
    Dit is ook de hoofdpagina, maar dan nadat je op edit hebt geklikt
    """
    match_history_table = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
    player_rating = Players.query.order_by(Players.rating.desc()).all()
    return render_template('match_history.html', match_history_table=match_history_table, match_id=match_id, Player_rating=player_rating)

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

    elif user_id_exists(player_2):
        rating_player_2 = Players.query.get(player_2).rating

    elif user_id_exists(player_2) == False:
        rating_player_2 = Players(user_id=player_2, rating=400)
        db.session.add(rating_player_2)
        db.session.commit()
    
    # In het geval een van de beide spelers nog niet bestond moeten ze 
    # eerst opnieuw opgehaald worden, vandaar deze statement
    if user_id_exists(player_1) and user_id_exists(player_2):
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
    new_match = MatchHistory(player_1=player_1, player_2=player_2, score_1=score_1, score_2=score_2)
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
