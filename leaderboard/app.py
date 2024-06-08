import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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
""" 
a string used to configure the connection to a database. Its typically in the format of a URL and includes the 
username, password, hostname, database name, and port number. The format of the URL is
dialect+driver://username:password@host:port/database.
"""
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "leaderboard.db")}'

# Hier wordt de app verteld dat het niet aanpassingen moet loggen in een apart bestand
# Dat zorgt namelijk voor overhead
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Maakt integratie tussen SQLAlchemy en de app
db = SQLAlchemy(app)

# Dit is een tabel 
class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_1 = db.Column(db.String(80), nullable=False)
    player_2 = db.Column(db.String(80), nullable=False)
    score_1 = db.Column(db.Integer, nullable=False)
    score_2 = db.Column(db.Integer, nullable=False)
# Create the database and tables within the application context
with app.app_context():
    db.create_all()

# De route decorator wordt gebruikt om Flask te vertellen welke URL de functie zou moeten triggeren
# HTML content in de string wordt gerenderd
@app.route('/')
def index():
    # lijst met matches
    leaderboard = Match.query.order_by(Match.score_1.desc()).all()
    # geeft een string terug van html waarin leaderbord is geinjecteerd waarvan de browser iets moois maakt
    # checken hoe render template werkt
    # roundtrip maken
    return render_template('leaderboard.html', leaderboard=leaderboard)

@app.route('/add', methods=['POST'])
def add_match():
    # spelers toevoegen, scores toevoegen -> ook in html ->table tennis  en in entry for leaderbord
    player_1 = request.form.get('player_1')
    player_2 = request.form.get('player_2')
    score_1 = request.form.get('score_1')
    score_2 = request.form.get('score_2')
    new_match = Match(player_1=player_1, player_2=player_2, score_1=score_1, score_2=score_2)
    db.session.add(new_match)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

# test
