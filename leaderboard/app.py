# TODO: rating progression ook opslaan als db?

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from sqlalchemy import and_, or_
import rating_module as rating_module 
import re
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio
from flask_bcrypt import Bcrypt 
import smtplib
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import settings
from the_big_username_blacklist import get_blacklist
from sqlalchemy.orm import Session

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

# Enter a secret key which can be any random string of characters, and is necessary as Flask-Login requires it to sign session cookies for protection again data tampering.
app.config["SECRET_KEY"] = settings.secret_key

# Hier wordt de app verteld dat het niet aanpassingen moet loggen in een apart bestand
# Dat zorgt namelijk voor overhead
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Itsdangerous serializer for generating tokens
s = URLSafeTimedSerializer(app.secret_key)

# LoginManager is needed for our application 
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Make bycrypt object to be able to hash passwords
bcrypt = Bcrypt(app) 


# Maakt integratie tussen SQLAlchemy en de app zodat je met python syntax interactie kan hebben met de app
# In simple terms, sqlalchemy() is a Python library that allows you to interact with your application’s 
# database using Python objects, rather than writing raw SQL code.
# When you use sqlalchemy() with a Flask object, it helps you to map your Python classes to the tables in 
# your database. This means you can create, read, update, and delete data in your database using Python objects, 
# without having to write SQL code.
db = SQLAlchemy(app)

#################################
## Databases 
################################

# Dit is een tabel in SQLite 
class MatchHistory(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    player_1 = db.Column(db.String(80), nullable=False)
    player_2 = db.Column(db.String(80), nullable=False)
    score_1 = db.Column(db.Integer, nullable=False)
    score_2 = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    rating_p1 = db.Column(db.Integer, nullable=True)
    rating_p2 = db.Column(db.Integer, nullable=True) 
    

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Create the database and tables within the application context
with app.app_context():
    db.create_all()

######################################
## Functions
######################################

@login_manager.user_loader
def loader_user(user_id):
	return db.session.get(Users, user_id) 
    
def user_id_exists(user_id):
    return bool(db.session.query(Users.query.filter_by(user_id=user_id).exists()).scalar())

def email_exists(email):
    return bool(db.session.query(Users.query.filter_by(email=email).exists()).scalar())

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
    
def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")
    
def is_blacklisted(username):
    # Define the blacklist
    blacklist = set(get_blacklist() + settings.blacklist)
                    
    # Check if any blacklisted term is a substring in the username
    for word in blacklist:
        if word.lower() in username.lower():
            return True
    return False
    

###################################
## Routes
###################################

@app.route('/register', methods=["GET", "POST"])
def register():
    pattern = r'^[a-zA-Z0-9]([._-]?[a-zA-Z0-9]+)*$'
    
    if request.method == 'POST':
        username = request.form.get("username")
        
        if re.fullmatch(pattern, username):
            
            if is_blacklisted(username):
                return f"'{username}' is blacklisted."
            
            else:
                new_user = Users(username=request.form.get("username"),
                        email=request.form.get("email"),
                        password=bcrypt.generate_password_hash(request.form.get("password")).decode('utf-8'))
                
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for("login"))

        else:
            return 'Username not valid'
    
    return render_template("sign_up.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # If a post request was made, find the user by 
    # filtering for the email
    
    if request.method == "POST":
        
        if email_exists(request.form.get("email")) == True:
            user = Users.query.filter_by(
                email=request.form.get("email")).first()
            
            if bool(user):
                # Check if the password entered is the 
                # same as the user's password
                if bcrypt.check_password_hash(user.password, request.form.get("password")):
                    login_user(user)
                    return redirect(url_for("index"))
            
            else:
                return 'password was incorrect'
        
        else:
            return 'email not found'
    return render_template("login.html")

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for("login"))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    
    # Gebruikers ophalen
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    users = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close() # Verbinding sluiten
    
    if request.method=='POST':      
        email = request.form.get('email')
        if email in users['email'].to_list():
            token = s.dumps(email, salt='password-reset-salt')  # Generate a token
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # Send email
            body = f"""
                    Hello,

                    Here is the reset link for your password:
                    {reset_link}

                    Kind regards,  
                    Caio from the Tabletennis webapp 
                    """
                    
            send_email(settings.subject, body, settings.sender, [email], settings.password)

            flash('A password reset link has been sent to your email.')
            return render_template('login.html')
            
        else:
            return 'Email address not found. Please try again.'
    
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Database pad
    db_path = settings.db_path
    
    # Gebruikers ophalen
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    users = pd.read_sql_query("SELECT * FROM users", conn) 
    conn.close() # Verbinding sluiten
    
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # Valid for 1 hour
    except SignatureExpired:
        return 'The password reset link has expired.'
    except BadSignature:
        return 'Invalid password reset link.'
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        
        # Hash the password for security
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Find the user and update their password
        if email in users['email'].to_list():
            users.loc[users['email'] == email, 'password'] = hashed_password  # Update the password
            flash('Your password has been reset successfully.')
        
            # Write the updated users DataFrame back to the database
            with sqlite3.connect(db_path) as conn:
                users.to_sql('users', conn, if_exists='replace', index=False)  # Save changes
                conn.commit()
            
            return redirect(url_for("login"))
        
        else:
            print('No user found, updating password was unsuccessful')

    return render_template('reset_password.html', token=token)


@app.route('/', methods=['GET'])
@login_required
def index():
    """
    Hiermee wordt de hoofdpagina geladen.
    Telkens als de hoofdpagina geladen wordt, worden de ratings opnieuw opgehaald.
    """
 
    # Hier wordt de tabel met ratings opgehaald
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn) # Ophalen van de gegevens die in de database zitten
    users = pd.read_sql_query("SELECT username FROM users", conn) # Ophalen van usernames voor de dropdown list
    conn.close() # Verbinding sluiten
    
    users = users['username'].to_list()

    # Ophalen van de meest recente player ratings
    player_rating = rating_module.most_recent_rating(match_history)
    
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
                MatchHistory.date.like(f'{date_search}%')
        )
        
    elif 'player' in request.args.keys() and bool(request.args['player']):
        player_name = request.args['player']
        match_history_table = MatchHistory.query.filter(or_(MatchHistory.player_1 == player_name, MatchHistory.player_2 == player_name))
        
    elif 'date' in request.args.keys() and bool(request.args['date']):
        date_search = request.args['date']
        match_history_table = MatchHistory.query.filter(MatchHistory.date.like(f'{date_search}%')) 
    
    else:      
        match_history_table = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
        
    # Filter voor de ratings
    if 'player_rating' in request.args.keys() and bool(request.args['player_rating']):
        player_name = request.args['player_rating']
        player_rating = player_rating[player_rating['Player'] == player_name] # In tegenstelling tot de wedstrijdgeschiedenis is deze data in de form van een df
        
    else:
        pass
    
    # Deze if handeld de edit knop op de homepagina hierbij wordt op dezelfde wijze als hierboven gekeken naar wat er in de GET request wordt gestuurd
    # maar dan wordt dat hier als bepalende factor voor de pagina layout gebruikt. (of invulvelden worden geladen met save en annuleren knoppen)
    if 'edit' in request.args.keys():
        match_id = int(request.args['edit'])
        return render_template('home.html', match_history_table=match_history_table, match_id=match_id, Player_rating=player_rating, invullen=invullen, users=users)
    
    return render_template('home.html', match_history_table=match_history_table, Player_rating=player_rating, invullen=invullen, users=users)

@app.route('/player_statistics', methods=['GET'])
@login_required
def index_player_stats():
    
    # Hier wordt de tabel met ratings opgehaald
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn) # Ophalen van de gegevens die in de database zitten
    users = pd.read_sql_query("SELECT username FROM users", conn) # Ophalen van usernames voor de dropdown list
    conn.close() # Verbinding sluiten
        
    users = users['username'].to_list()
    stats = rating_module.player_statistics(match_history)
    rating_progression = rating_module.player_rating_progression(match_history)
    
    if 'player' in request.args.keys() and bool(request.args['player']):
        player_name = request.args['player']
        stats = stats[stats['Player'] == player_name]
    else:
        pass

    # Initialize an empty figure
    fig = go.Figure()

    # Create a trace for each player
    for player in rating_progression['Player'].unique():
        player_data = rating_progression[rating_progression['Player'] == player]
        fig.add_trace(go.Scatter(
            x=player_data['Date'],
            y=player_data['Rating'],
            mode='lines+markers',
            name=player
        ))
        
        fig.update_layout(
            title='Player Rating Progression Over Time',
            xaxis_title='Date',
            yaxis_title='Rating'
    )

    # Convert the figure to JSON for rendering in the template
    graphJSON = pio.to_json(fig)

    # Pass the JSON data to the template
    return render_template('player_statistics.html', graphJSON=graphJSON, stats=stats, users=users)


# Deze URL kan je niet bezoeken, maar dient alleen om iets in te voeren vandaar de methode POST
@app.route('/add', methods=['POST'])
@login_required
def add_match():
    """ 
    Dit is de pagina waarin een post verstuurd wordt naar de server met de wedstrijd input.
    Na het binnenkrijgen van de wedstrijdgegevens wordt hier aan de backend ook een nieuwe berekening gemaakt van de ratings.
    """
    # Hier wordt de informatie opgehaald uit de velden
    player_1 = current_user.username
    player_2 = request.form.get('player_2')
    score_1 = int(request.form.get('score_1'))
    score_2 = int(request.form.get('score_2'))
    date = datetime.strptime(request.form.get('datetime'), "%Y-%m-%dT%H:%M")
    
    if date >= datetime.now():
        return 'Mag niet in de toekomst zijn'
    
    # Controle op gelijkspel
    if score_1 == score_2:
        return 'Score mag niet gelijk zijn'
    else:
        pass
    
    # Controle op naam
    if player_1 == player_2:
        return 'Spelersnamen mogen niet hetzelfde zijn'
    else:
        pass
    
    # Controle op verschil score
    if abs(score_1 - score_2) < 2:
        return 'Scoreverschil moet 2 of groter zijn'
    else:
        pass
    
    # Hier worden de ratings opnieuw berekend
    # Verbinden en ophalen van huidige database
    conn = sqlite3.connect(settings.db_path)
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    conn.close()
    
    # Hier wordt een match_id gemaakt voor de nieuwe wedstrijd, omdat elke match een unieke id heeft
    if len(match_history['match_id']) == 0:
        new_id = 1
    else:
        new_id = int(match_history['match_id'].max() + 1)
    
    # Hier wordt een df gemaakt met de gegevens van de nieuwe match waarbij de kolommen met de ratings leeg blijven
    new_row = pd.DataFrame({
        'match_id': new_id,
        'player_1': player_1,
        'player_2': player_2,
        'score_1': score_1,
        'score_2': score_2,
        'date': date,
        'rating_p1': '',
        'rating_p2': ''
    }, index=[0])
    
    match_history['date'] = pd.to_datetime(match_history['date']) # Datum kolom omzetten naar datetime
    
    # Hier wordt de nieuwe rij aan de huidige wedstrijdgeschiedenis toegevoegd
    match_history = pd.concat([match_history, new_row], ignore_index=True).sort_values('date', ascending=True)

    # Ratings verversen
    match_history = rating_module.calculate_ratings(match_history)
    
    # Hier wordt de nieuwe versie weggeschreven naar de database
    conn = sqlite3.connect(settings.db_path)
    match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    conn.close()
    return redirect(url_for('index'))


@app.route('/update/<int:match_id>', methods=['POST'])
@login_required
def update_item(match_id):
    """
    Deze pagina wordt gebruikt voor het aanpassen van een bestaande uitslag. 
    Na het ophalen van de wedstrijdgegevens die geupdate moet worden de updates toegepast en de ratings opnieuw berekend voordat
    er een redirect is naar de homepage.
    """
    # Ophalen van wedstrijd die aangepast moet worden adhv match id
    # match_to_update = MatchHistory.query.get(match_id)
    conn = sqlite3.connect(settings.db_path)
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
        score_1 = int(match_to_update.score_1.iloc[0])

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
    
    id = match_to_update['match_id'][0]
    match_history.loc[match_history['match_id'] == id] = match_to_update.iloc[0].values

    # Ratings verversen
    match_history = rating_module.calculate_ratings(match_history)

    # Dit is ter zekerheid dat de bestandstypes goed zijn
    match_history['score_1'] = match_history['score_1'].astype(int)
    match_history['score_2'] = match_history['score_2'].astype(int)

    # Hier wordt de nieuwe versie weggeschreven naar de database
    conn = sqlite3.connect(settings.db_path)
    match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete/<int:match_id>', methods=['GET'])
@login_required
def delete_item(match_id):
    
    # Ophalen van wedstrijd die aangepast moet worden adhv match id
    # match_to_update = MatchHistory.query.get(match_id)
    conn = sqlite3.connect(settings.db_path)
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    match_to_update = pd.read_sql_query(f"SELECT * FROM match_history WHERE match_id = {match_id}", conn)
    conn.close()
    
    # Wedstrijd eruit halen
    match_history = match_history[match_history['match_id'] != match_id]
    
    # Match_id's lopen niet perfect meer op omdat een getal mist wanneer een match_id niet de nieuwste was
    # Daarom de id's resetten voordat ze weer naar de database gestuurd worden
    nieuwe_ids = list(range(1,len(match_history['match_id']) + 1))
    match_history['match_id'] = nieuwe_ids
    
    # Ratings verversen
    match_history = rating_module.calculate_ratings(match_history)

    # Hier wordt de nieuwe versie weggeschreven naar de database
    conn = sqlite3.connect(settings.db_path)
    match_history.to_sql('match_history', conn, if_exists='replace', index=False)
    conn.close()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    