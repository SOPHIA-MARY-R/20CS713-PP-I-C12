# -*- encoding: utf-8 -*-


from app import app, db
from flask import Flask

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)