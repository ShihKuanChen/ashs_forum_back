import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, or_
from dotenv import load_dotenv

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
    ...


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
            "article_upload_time": article.article_upload_time
        })
    
    return result

@app.route("/api/login")
def login():
    ...

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)
