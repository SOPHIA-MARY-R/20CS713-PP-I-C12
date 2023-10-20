from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "College Recommendation System"

#  Run Command: flask --app app run