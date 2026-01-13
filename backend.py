from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class User(db.Modle):
    id = db.Column(db.Integer, primary_key=True)

@app.route("/<board>/<id>")
def get_article(board, id):
    ...

@app.route("/api")
def get_titles(board):
    limit = request.args.get('limit', default=30, type=int)
    start_id = request.args.get('start_id')
    board = request.args.get('board')
