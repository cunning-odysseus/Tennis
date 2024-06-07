import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Define the absolute path for the database directory
base_dir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(base_dir, 'data')

# Ensure the 'data' directory exists
if not os.path.exists(db_dir):
    os.makedirs(db_dir)

# Update the database URI to point to the 'data' directory with an absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(db_dir, "leaderboard.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, nullable=False)

# Create the database and tables within the application context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    leaderboard = Match.query.order_by(Match.score.desc()).all()
    return render_template('leaderboard.html', leaderboard=leaderboard)

@app.route('/add', methods=['POST'])
def add_match():
    player = request.form.get('player')
    score = request.form.get('score')
    new_match = Match(player=player, score=int(score))
    db.session.add(new_match)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

# test
