import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    
# Create the database and tables within the application context
with app.app_context():
    db.create_all()

# De route decorator wordt gebruikt om Flask te vertellen welke URL de functie zou moeten triggeren
# HTML content in de string wordt gerenderd
# @route verteld wat er moet worden laten zien wanneer je een bepaalde URL gebruikt in je browser
# Hier staat / -> dus wanneer de hoofdpagina (index page) geladen wordt, dan wordt dit laten zien
# TODO uitzoeken wat escape doet 
@app.route('/<int:match_id>')
def index(match_id):
    # lijst met matches
    leaderboard = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
    # geeft een string terug van html waarin leaderbord is geinjecteerd waarvan de browser iets moois maakt
    # checken hoe render template werkt
    # roundtrip maken
    # TODO varname veranderen
    
    if match_id:
        match_to_update = MatchHistory.query.get_or_404(match_id)
    return render_template('match_history.html', leaderboard=leaderboard, match_id=match_id)

# Deze URL kan je niet bezoeken, maar dient alleen om iets in te voeren vandaar de methode POST
@app.route('/add', methods=['POST'])
def add_match():
    # spelers toevoegen, scores toevoegen -> ook in html ->table tennis  en in entry for leaderbord
    player_1 = request.form.get('player_1')
    player_2 = request.form.get('player_2')
    score_1 = request.form.get('score_1')
    score_2 = request.form.get('score_2')
    new_match = MatchHistory(player_1=player_1, player_2=player_2, score_1=score_1, score_2=score_2)
    db.session.add(new_match)
    db.session.commit()
    return redirect(url_for('index'))

# TODO kijken of get en post nodig zijn
@app.route('/update/<int:match_id>', methods=['GET', 'POST'])
def update_item(match_id):
    match_to_update = MatchHistory.query.get_or_404(match_id)
    if request.method == 'POST':
        match_to_update.player_1 = request.form['player_1']
        match_to_update.player_2 = request.form['player_2']
        match_to_update.score_1 = request.form['score_1']
        match_to_update.score_2 = request.form['score_2']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', match_to_update=match_to_update)

# Voorbeeld van een dynamische route
@app.route('/user/<string:username>') 
def show_user(username): 
    # Greet the user 
    return f'Hello {username} !'

if __name__ == '__main__':
    app.run(debug=True)

