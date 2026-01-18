import os
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, String, select
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass, Mapped, mapped_column
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime
from typing import Mapping, Any

# load .env file
load_dotenv()

app = Flask(__name__)

# set sql
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = os.getenv('SECRET_KEY')


class Base(DeclarativeBase, MappedAsDataclass):
    pass

db = SQLAlchemy(app, model_class=Base)

# class User(db.Model, Base):
#     __tablename__ = 'users'
#     user_id: Mapped[int] = mapped_column(primary_key=True)
#     user_name: Mapped[str] = mapped_column(nullable=False)
#     user_email: Mapped[str] = mapped_column(nullable=False)

    # user_id = db.Column(db.BigInteger, primary_key=True)
    # user_name = db.Column(db.String(80))
    # user_email = db.Column(db.String(80))

class Article(db.Model, Base):
    __tablename__ = 'articles'
    article_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    article_board: Mapped[str] = mapped_column(String(50), nullable=False)
    article_title: Mapped[str] = mapped_column(String(50), nullable=False)
    article_content: Mapped[str] = mapped_column(Text, nullable=False)
    article_upload_time: Mapped[str] = mapped_column(String(50), nullable=False)
    writer_id: Mapped[str] = mapped_column(String(80), nullable=False)
    pinned: Mapped[bool] = mapped_column(nullable=False, default=False)


class Comment(db.Model, Base):
    __tablename__ = 'comments'
    comment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    article_id: Mapped[int] = mapped_column(nullable=False)
    comment_content: Mapped[str] = mapped_column(Text, nullable=False)
    comment_upload_time: Mapped[str] = mapped_column(String(50), nullable=False)
    writer_id: Mapped[str] = mapped_column(String(80), nullable=False)


class Board(db.Model, Base):
    __tablename__ = 'boards'
    board_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    board_eng: Mapped[str] = mapped_column(String(50), nullable=False)
    board_zh: Mapped[str] = mapped_column(String(50), nullable=False)
    board_n_articles: Mapped[int] = mapped_column(nullable=False)
    board_last_time: Mapped[str] = mapped_column(String(50), nullable=False)


@app.route("/api/boards", methods=['GET'])
def get_boards():
    boards = db.session.execute(select(Board)).scalars().all()

    result: list[dict[str, str | int]] = []
    for board in boards:
        result.append({
            "board_id": board.board_id,
            "board_eng": board.board_eng,
            "board_zh": board.board_zh,
            "board_n_articles": board.board_n_articles,
            "board_last_time": board.board_last_time
        })
    
    return jsonify(result)

@app.route("/api/board_zh", methods=['GET'])
def get_board_zh():
    board_eng = request.args.get('board')
    board_zh = db.session.execute(
        select(Board.board_zh).where(Board.board_eng == board_eng)
    ).scalar()

    return jsonify({"board_zh": board_zh})


@app.route("/api/article/<int:article_id>", methods=['GET'])
def get_article(article_id: int):
    article = db.session.get(Article, article_id)
    
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
    
    current_time = datetime.now()
    
    request_data = request.get_json()

    article_board = request_data['article_board']
    article_content = request_data['article_content']
    article_title = request_data['article_title']
    writer_id = session['user_id']
    pinned = request_data['pinned'] if session.get('is_manager') else False

    if article_title.strip() == "" or article_content.strip() == "":
        return jsonify({"error": "Title and content cannot be empty"}), 400

    new_article = Article(
        article_board=article_board,
        article_content=article_content,
        article_title=article_title,
        article_upload_time=current_time.strftime("%Y-%m-%d %H:%M"),
        writer_id=writer_id,
        pinned=pinned
    )

    db.session.add(new_article)

    board_data = db.session.execute(
        select(Board).where(Board.board_eng == article_board)
    ).scalar_one()

    board_data.board_n_articles += 1
    board_data.board_last_time = current_time.strftime("%Y-%m-%d")
    
    try:
        db.session.commit()

        return jsonify({"message": "Article created successfully"}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/api/write_comment", methods=['POST'])
def create_comment():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    current_time = datetime.now()
    
    request_data: dict[str, str] = request.get_json()

    article_id = int(request_data['article_id'])
    comment_content = request_data['comment_content']
    writer_id = session['user_id']

    if comment_content.strip() == "":
        return jsonify({"error": "Content cannot be empty"}), 400

    new_comment = Comment(
        article_id=article_id,
        comment_content=comment_content,
        writer_id=writer_id,
        comment_upload_time=current_time.strftime("%Y-%m-%d %H:%M")
    )

    db.session.add(new_comment)

    try:
        db.session.commit()

        return jsonify({"message": "Comment created successfully"}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/comments/<int:article_id>", methods=['GET'])
def get_comments(article_id: int):
    comments = (
        db.session
        .execute(
            select(Comment)
            .where(Comment.article_id == article_id)
            .order_by(Comment.comment_id.asc())
        )
        .scalars()
        .all()
    )
    result: list[dict[str, str | int]] = []

    for comment in comments:
        result.append({
            "comment_id": comment.comment_id,
            "comment_content": comment.comment_content,
            "comment_upload_time": comment.comment_upload_time,
        })

    return jsonify(result)

@app.route("/api", methods=['GET'])
def get_articles_info():
    limit = request.args.get('limit', default=30, type=int)
    last_id = request.args.get('last_id', default=-1, type=int)
    board = request.args.get('board')

    result: list[dict[str, str | int]] = []

    if last_id == -1:
        pinned_stmt = (
            select(Article)
            .where(Article.pinned == True)
            .where(Article.article_board == board)
            .order_by(Article.article_id.desc())
        )

        pinned_articles = db.session.execute(pinned_stmt).scalars().all()

        for article in pinned_articles:
            result.append({
                "article_title": article.article_title,
                "article_upload_time": article.article_upload_time,
                "article_id": article.article_id
            })

    stmt = select(Article)

    if last_id != -1:
        stmt = stmt.where(Article.article_id < last_id)

    stmt = (
        stmt
        .where(Article.article_board == board)
        .where(Article.pinned == False)
        .order_by(Article.article_id.desc())
        .limit(limit)
    )

    articles = db.session.execute(stmt).scalars().all()
    
    for article in articles:
        result.append({
            "article_title": article.article_title,
            "article_upload_time": article.article_upload_time,
            "article_id": article.article_id
        })
    
    return jsonify(result)

@app.route("/api/login", methods=['POST'])
def login():
    request_data: dict[str, str] = request.get_json()
    token = request_data.get('token')

    try:
        id_info: Mapping[str, Any] = id_token.verify_oauth2_token( # type: ignore
            token,
            requests.Request(),
            os.getenv('CLIENT_ID')
        )

        if (id_info.get('hd') != os.getenv('HD')):
            print(id_info.get('hd'))
            print(os.getenv('HD'))
            return jsonify({"error": "Invalid domain"}), 401
        
        session['user_id'] = id_info['sub']
        session['user_name'] = id_info['name']
        session['user_email'] = id_info['email']
        session['logged_in'] = True

        managers_email = os.getenv('MANAGERS').split() # type: ignore
        session['is_manager'] = id_info['email'] in managers_email
        # session['is_manager'] = False
    
        return jsonify({"message": "Login successful"}), 200
        
    except ValueError:
        return jsonify({"error": "Invalid token"}), 401

@app.route("/api/is_logged_in", methods=['GET'])
def is_logged_in():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({"message": "Login successful"}), 200
    
@app.route("/api/logout", methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@app.route("/api/is_manager", methods=['GET'])
def is_manager():
    if session.get('is_manager'):
        return jsonify(True), 200
    
    return jsonify(False), 401



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)
