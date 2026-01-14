import os
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, or_
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

# load .env file
load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# class User(db.Modle):
#     __tablename__ = 'users'
#     user_id = db.Column(db.BigInteger, primary_key=True)
#     user_name = db.Column(db.String(80))
#     user_email = db.Column(db.String(80))

class Article(db.Model):
    __tablename__ = 'articles'
    article_id = db.Column(db.BigInteger, primary_key=True)
    article_board = db.Column(db.String(80))
    article_title = db.Column(db.String(80))
    article_content = db.Column(db.Text)
    article_upload_time = db.Column(db.String(50))
    writer_id = db.Column(db.BigInteger)

@app.route("/api/article/<int:id>", methods=['GET'])
def get_article(id):
    article = db.session.get(Article, id)
    
    if article is None:
        return jsonify({"error": "Can't find the article."}), 404
    
    return jsonify({
        "article_id": article.article_id,
        "article_title": article.article_title,
        "article_content": article.article_content,
        "article_upload_time": article.article_upload_time
    })

@app.route("/api/write", methods=['POST'])
def create_article():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    request_data = request.get_json()


@app.route("/api", methods=['GET'])
def get_titles():
    limit = request.args.get('limit', default=30, type=int)
    start_id = request.args.get('start_id')
    board = request.args.get('board')

    stmt = (
        db.select(Article)
        .where(or_(Article.article_id < start_id, start_id == -1))
        .where(Article.article_board == board)
        .order_by(desc(Article.article_id))
        .limit(limit)
    )

    articles = db.session.execute(stmt).scalars().all()

    result = []
    for article in articles:
        result.append({
            "article_title": article.article_title,
            "article_upload_time": article.article_upload_time,
            "article_id": article.article_id
        })
    
    return result

@app.route("/api/login", methods=['POST'])
def login():
    request_data = request.get_json()
    token = request_data['token']

    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), os.getenv('CLIENT_ID'))
        session['user_id'] = id_info['sub']
        session['user_name'] = id_info['name']
        session['user_email'] = id_info['email']
        session['logged_in'] = True 
    
        return jsonify({"message": "Login successful"}), 200
        
    except ValueError:
        return jsonify({"error": "Invalid token"}), 401

@app.route("/api/is_logged_in", methods=['GET'])
def login():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({"message": "Login successful"}), 200
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)
