from flask import Flask, render_template
import os
from dotenv import load_dotenv

load_dotenv("C:/Users/alber/PycharmProjects/EnviromentalVariables/.env")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")

@app.route('/')
def home():

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)