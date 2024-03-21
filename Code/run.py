# -*- encoding: utf-8 -*-


from app import app, db
from flask import Flask
from flask_cors import CORS, cross_origin

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)