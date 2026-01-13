from flask import Flask, request

app = Flask(__name__)

@app.route("/<board>/<id>")
def get_article(board, id):
    ...

@app.route("/api")
def get_titles(board):
    limit = request.args.get('limit', default=30, type=int)
    start_id = request.args.get('start_id')
    board = request.args.get('board')

