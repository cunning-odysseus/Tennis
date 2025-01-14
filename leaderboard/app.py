# TODO: db naam aanpassen
# TODO: navbalk vastzetten op pagina ook tijdens scrollen?

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from sqlalchemy import and_, or_
import module 
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

# Hier wordt een flask object gemaakt met de naam "app"
app = Flask(__name__)

# Hier wordt het huidige pad opgehaald
base_dir = os.path.abspath(os.path.dirname(__file__))

# Hier wordt de string van een nieuw pad gemaakt in de huidige directory
db_dir = os.path.join(base_dir, "data")

# Hier wordt het pad gemaakt als het nog niet bestaat
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# De app vertellen waar de database staat en wat voor database het is

# a string used to configure the connection to a database. Its typically in the format of a URL and includes the 
# username, password, hostname, database name, and port number. The format of the URL is
# dialect+driver://username:password@host:port/database.
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(db_dir, 'data.db')}"

# Enter a secret key which can be any random string of characters, and is necessary as Flask-Login requires it to sign session cookies for protection again data tampering.
app.config["SECRET_KEY"] = settings.secret_key

# Hier wordt de app verteld dat het niet aanpassingen moet loggen in een apart bestand
# Dat zorgt namelijk voor overhead
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Itsdangerous serializer for generating tokens
s = URLSafeTimedSerializer(app.secret_key)

# LoginManager is needed for our application 
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
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

def invullen(regelid):
    if len(request.args.keys()) == 0:
        return f"{request.url}?edit={regelid}"
    elif re.search(r"[?&]edit=", request.url):
        return re.sub(r"edit=[0-9]+", "edit=" + str(regelid), request.url)
    else:
        return f"{request.url}&edit={regelid}"
    
def send_email(subject, body, sender, recipients, password):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")
    
def is_blacklisted(username):
    blacklist = []#get_blacklist()
                    
    for word in blacklist:
        if word.lower() in username.lower():
            return True
    return False

###################################
## Routes
#################################### 

# De route decorator wordt gebruikt om Flask te vertellen welke URL de functie zou moeten triggeren
# HTML content in de string wordt gerenderd
# @route verteld wat er moet worden laten zien wanneer je een bepaalde URL gebruikt in je browser
# Hier staat / -> dus wanneer de hoofdpagina (index page) geladen wordt, dan wordt dit laten zien   

@app.route("/register", methods=["GET", "POST"])
def register():
    """ Pagina waar nieuwe gebruikers zich kunnen aanmelden """
    
    # Username voorwaarden in regex
    pattern = r"^[a-zA-Z0-9]([._-]?[a-zA-Z0-9]){2,14}$"
    
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        password_check = request.form.get("password_check")
        
        # email valideren
        if email_exists(email):
            flash("Email already exists")
            return render_template("sign_up.html")
        
        # username valideren
        if not re.fullmatch(pattern, username):
            flash("Username not valid. It should contain only letters, numbers, dots, underscores, or hyphens.")
            return render_template("sign_up.html")
        
        # Check op username
        if is_blacklisted(username):
            flash(f"'{username}' is blacklisted.")
            return render_template("sign_up.html")
        
        # Check of wachtwoord overeen komt met de wachtwoord check
        if password != password_check:
            flash("Passwords did not match.")
            return render_template("sign_up.html")
        
        # Hash wachtwoord en maak nieuwe gebruiker aan
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user = Users(username=username, email=email, password=hashed_password)
        
        try:
            # nieuwe gebruiker toevoegen
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
        
        except Exception as e:
            # error handelen
            db.session.rollback()
            flash("An error occurred while trying to register. Please try again.")
            print(f"Error: {e}")  # Log the error for debugging
            
            return render_template("sign_up.html")
    
    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Pagina waar gebruikers kunnen inloggen"""
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if email exists
        user = Users.query.filter_by(email=email).first()
        
        if user:
            # Check if the password matches
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for("index"))
            else:
                flash("Password was incorrect")
                return render_template("login.html", email=email)
        else:
            flash("Email not found")
            return render_template("login.html", email=email)
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("login"))


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Pagina waar gebruikers een aanvraag tot wijziging van hun wachtwoord kunnen indienen"""
    
    if request.method == "POST":      
        email = request.form.get("email")
        
        # Check if email exists in the database
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
        user_exists = cursor.fetchone() is not None
        conn.close()
        
        if user_exists:
            # Generate token for password reset
            token = s.dumps(email, salt="password-reset-salt")  
            reset_link = url_for("reset_password", token=token, _external=True)
            
            # Send email with reset link
            body = f"""
                    Hello,

                    Here is the reset link for your password:
                    {reset_link}

                    Kind regards,
                    Caio from the Table Tennis webapp
                    """
                    
            send_email(settings.subject, body, settings.sender, [email], settings.password)

            flash("A password reset link has been sent to your email.")
            return redirect(url_for("login"))  # Redirect to login after sending email
            
        else:
            flash("Email address not found. Please try again.")
            return redirect(url_for("forgot_password"))  # Stay on the forgot password page if email is not found
    
    return render_template("forgot_password.html")  # Render forgot password form if method is GET


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Pagina voor wachtwoord reset via een unieke link"""

    try:
        # Decode de token om het emailadres te verkrijgen; geldig voor 1 uur
        email = s.loads(token, salt="password-reset-salt", max_age=3600)
    except SignatureExpired:
        flash("The password reset link has expired. Please request a new one.")
        return redirect(url_for("forgot_password"))
    except BadSignature:
        flash("Invalid password reset link.")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        # Nieuw wachtwoord ophalen vanuit het formulier
        new_password = request.form.get("new_password")
        
        # Hash het nieuwe wachtwoord
        hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
        
        # Update het wachtwoord van de gebruiker in de database
        conn = sqlite3.connect(settings.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
        conn.commit()
        conn.close()
        
        flash("Your password has been reset successfully. You can now log in with your new password.")
        return redirect(url_for("login"))
    
    # Render de pagina om het wachtwoord te resetten, inclusief de token in de context
    return render_template("reset_password.html", token=token)

@app.route("/", methods=["GET"])
@login_required
def index():
    """
    Hiermee wordt de hoofdpagina geladen.
    Telkens als de hoofdpagina geladen wordt, worden de ratings opnieuw opgehaald.
    """
 
    # Hier wordt de tabel met ratings opgehaald
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn) # Ophalen van de gegevens die in de database zitten
    users = pd.read_sql_query("SELECT id, username FROM users", conn) # Ophalen van usernames voor de dropdown list
    conn.close() # Verbinding sluiten
    
    users = users[["id","username"]]

    # Ophalen van de meest recente player ratings
    player_rating = module.most_recent_rating(match_history)
    
    # De volgende if / else zijn er om de filter op de tabel te handelen
    
    # Als er in de filter een speler en een datum wordt meegegeven wordt er een GET request gestuurd met daarin de speler en datum in de payload.
    # In de URL staat de speler en de datum en daarom wordt er hier met request.args.keys() gekeken wat dan meegestuurd is. Deze filosofie wordt ook
    # bij de gevallen van enkel speler, enkel datum of niks toegepast.
    if ("player" in request.args.keys() and bool(request.args["player"])) and ("date" in request.args.keys() and bool(request.args["date"])):
        player_name = request.args["player"]
        date_search = request.args["date"]
        match_history_table = MatchHistory.query.filter(
            and_
                (or_(MatchHistory.player_1 == player_name, MatchHistory.player_2 == player_name)),
                MatchHistory.date.like(f"{date_search}%")
        )
        
    elif "player" in request.args.keys() and bool(request.args["player"]):
        player_name = request.args["player"]
        match_history_table = MatchHistory.query.filter(or_(MatchHistory.player_1 == player_name, MatchHistory.player_2 == player_name))
        
    elif "date" in request.args.keys() and bool(request.args["date"]):
        date_search = request.args["date"]
        match_history_table = MatchHistory.query.filter(MatchHistory.date.like(f"{date_search}%")) 
    
    else:      
        match_history_table = MatchHistory.query.order_by(MatchHistory.date.desc()).all()
        
    # Filter voor de ratings
    if "player_rating" in request.args.keys() and bool(request.args["player_rating"]):
        player_name = request.args["player_rating"]
        player_rating = player_rating[player_rating["Player"] == player_name] # In tegenstelling tot de wedstrijdgeschiedenis is deze data in de form van een df
        
    else:
        pass
    
    # Deze if handeld de edit knop op de homepagina hierbij wordt op dezelfde wijze als hierboven gekeken naar wat er in de GET request wordt gestuurd
    # maar dan wordt dat hier als bepalende factor voor de pagina layout gebruikt. (of invulvelden worden geladen met save en annuleren knoppen)
    if "edit" in request.args.keys():
        match_id = int(request.args["edit"])
        return render_template("home.html", match_history_table=match_history_table, match_id=match_id, Player_rating=player_rating, invullen=invullen, users=users, c_user=current_user.username, email_admin=settings.email_admin)
    
    return render_template("home.html", match_history_table=match_history_table, Player_rating=player_rating, invullen=invullen, users=users, c_user=current_user.username, email_admin=settings.email_admin)

@app.route("/player_statistics", methods=["GET"])
@login_required
def index_player_stats():
    """ Dit is de pagina met spelersstatistieken """
    
    # Hier wordt de tabel met ratings opgehaald
    conn = sqlite3.connect(settings.db_path) # Verbinding maken met de database
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn) # Ophalen van de gegevens die in de database zitten
    users = pd.read_sql_query("SELECT username FROM users", conn) # Ophalen van usernames voor de dropdown list
    conn.close() # Verbinding sluiten
        
    users = users["username"].to_list()
    stats = module.player_statistics(match_history)
    rating_progression = module.player_rating_progression(match_history)
    user_performance = module.performance_vs_others(match_history, current_user.username)
    
    # filter voor de player  table
    if "player" in request.args.keys() and bool(request.args["player"]):
        player_name = request.args["player"]
        stats = stats[stats["Player"] == player_name]
    else:
        pass
    
    # filter voor de performance vs others table
    if "opponent" in request.args.keys() and bool(request.args["opponent"]):
        opponent = request.args["opponent"]
        print(opponent)
        user_performance = user_performance[user_performance["Opponent"] == opponent] # In tegenstelling tot de wedstrijdgeschiedenis is deze data in de form van een df
        
    else:
        print('opponent not found')
        pass

    # Initialize an empty figure
    fig = go.Figure()

    # Create a trace for each player
    for player in rating_progression["Player"].unique():
        player_data = rating_progression[rating_progression["Player"] == player]
        fig.add_trace(go.Scatter(
            x=player_data["Date"],
            y=player_data["Rating"],
            mode="lines+markers",
            name=player
        ))
        
        fig.update_layout(
            title="Player Rating Progression Over Time",
            xaxis_title="Date",
            yaxis_title="Rating"
    )

    # Convert the figure to JSON for rendering in the template
    graphJSON = pio.to_json(fig)

    # Pass the JSON data to the template
    return render_template("player_statistics.html", graphJSON=graphJSON, stats=stats, users=users, user_performance=user_performance, c_user=current_user.username)

@app.route("/about", methods=["GET"])
@login_required
def about():
    """ Pagina met info over de website """
    return render_template("about.html")


# Deze URL kan je niet bezoeken, maar dient alleen om iets in te voeren vandaar de methode POST
@app.route("/add", methods=["POST"])
@login_required
def add_match():
    """ 
    Dit is de pagina waarin een post verstuurd wordt naar de server met de wedstrijd input.
    Na het binnenkrijgen van de wedstrijdgegevens wordt hier aan de backend ook een nieuwe berekening gemaakt van de ratings.
    """
     # Ophalen van wedstrijdgegevens uit de formuliervelden
    player_1 = current_user.username
    player_2 = request.form.get("player_2")
    score_1 = int(request.form.get("score_1"))
    score_2 = int(request.form.get("score_2"))
    date = datetime.strptime(request.form.get("datetime"), "%Y-%m-%dT%H:%M")
    
    # Valideren van de wedstrijdgegevens
    if date > datetime.now():
        flash("Date cannot be in the future.")
        return redirect(url_for("index"))
    
    if score_1 == score_2:
        flash("Scores cannot be tied.")
        return redirect(url_for("index"))
    
    if player_1 == player_2:
        flash("Players cannot have the same name.")
        return redirect(url_for("index"))
    
    if abs(score_1 - score_2) < 2:
        flash("Score difference must be at least 2.")
        return redirect(url_for("index"))
    
    if (score_1 > 11 or score_2 > 11) and abs(score_1 - score_2) > 2:
        flash("Score difference can only be 2 when playing over 11 points")
        return redirect(url_for("index"))
    
    if score_1 < 11 and score_2 < 11:
        flash("A game is played until at least 11 points.")
        return redirect(url_for("index"))
    
    else:
        pass


    # Verbinden met de database en ophalen van de huidige wedstrijdgeschiedenis
    with sqlite3.connect(settings.db_path) as conn:
        match_history = pd.read_sql_query("SELECT * FROM match_history", conn)

    # Genereer een unieke `match_id`
    new_id = int(match_history["match_id"].max() + 1) if not match_history.empty else 1

    # Maak een nieuwe rij voor de nieuwe wedstrijd
    new_row = pd.DataFrame({
        "match_id": [new_id],
        "player_1": [player_1],
        "player_2": [player_2],
        "score_1": [score_1],
        "score_2": [score_2],
        "date": [date],
        "rating_p1": [""],  # Plaatsvervanger voor bijgewerkte ratings
        "rating_p2": [""]
    })

    # Voeg de nieuwe rij toe aan de huidige wedstrijdgeschiedenis en sorteer op datum
    match_history["date"] = pd.to_datetime(match_history["date"])
    match_history = pd.concat([match_history, new_row], ignore_index=True).sort_values("date")

    # Herbereken de ratings
    match_history = module.calculate_ratings(match_history)

    # Sla de bijgewerkte wedstrijdgeschiedenis op in de database
    with sqlite3.connect(settings.db_path) as conn:
        match_history.to_sql("match_history", conn, if_exists="replace", index=False)

    flash("Match added and ratings updated.")
    return redirect(url_for("index"))


@app.route("/update/<int:match_id>", methods=["POST"])
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
    if bool(request.form.get("player_1")) == True:
        player_1 = request.form.get("player_1")
    else:
        player_1 = match_to_update.player_1
    
    if bool(request.form.get("player_2")) == True:  
        player_2 = request.form.get("player_2")
    else:
        player_2 = match_to_update.player_2

    if bool(request.form.get("score_1")) == True:
        score_1 = int(request.form.get("score_1"))
    else:
        score_1 = int(match_to_update.score_1.iloc[0])

    if bool(request.form.get("score_2")) == True:
        score_2 = int(request.form.get("score_2"))

    else:
        score_2 = int(match_to_update.score_2)
    
    # Controle of de scores niet gelijk zijn.
    if score_1 == score_2:
        flash("Scores cannot be equal")
        return redirect(url_for("index"))
    else:
        pass
    
    match_to_update["player_1"] = player_1
    match_to_update["player_2"] = player_2
    match_to_update["score_1"] = score_1
    match_to_update["score_2"] = score_2
    
    id = match_to_update["match_id"][0]
    match_history.loc[match_history["match_id"] == id] = match_to_update.iloc[0].values

    # Ratings verversen
    match_history = module.calculate_ratings(match_history)

    # Dit is ter zekerheid dat de bestandstypes goed zijn
    match_history["score_1"] = match_history["score_1"].astype(int)
    match_history["score_2"] = match_history["score_2"].astype(int)

    # Hier wordt de nieuwe versie weggeschreven naar de database
    conn = sqlite3.connect(settings.db_path)
    match_history.to_sql("match_history", conn, if_exists="replace", index=False)
    conn.close()
    
    return redirect(url_for("index"))

@app.route("/delete/<int:match_id>", methods=["GET"])
@login_required
def delete_item(match_id):
    """ Deze pagina kan alleen bezocht worden door de beheerder ter behoeve van het verwijderen van een wedstrijd """
    
    # Ophalen van wedstrijd die aangepast moet worden adhv match id
    # match_to_update = MatchHistory.query.get(match_id)
    conn = sqlite3.connect(settings.db_path)
    match_history = pd.read_sql_query("SELECT * FROM match_history", conn)
    match_to_update = pd.read_sql_query(f"SELECT * FROM match_history WHERE match_id = {match_id}", conn)
    conn.close()
    
    # Wedstrijd eruit halen
    match_history = match_history[match_history["match_id"] != match_id]
    
    # Match_id"s lopen niet perfect meer op omdat een getal mist wanneer een match_id niet de nieuwste was
    # Daarom de id"s resetten voordat ze weer naar de database gestuurd worden
    nieuwe_ids = list(range(1,len(match_history["match_id"]) + 1))
    match_history["match_id"] = nieuwe_ids
    
    # Ratings verversen
    match_history = module.calculate_ratings(match_history)

    # Hier wordt de nieuwe versie weggeschreven naar de database
    conn = sqlite3.connect(settings.db_path)
    match_history.to_sql("match_history", conn, if_exists="replace", index=False)
    conn.close()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
    