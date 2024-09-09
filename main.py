from flask import Flask, render_template
import os
from dotenv import load_dotenv

load_dotenv("C:/Users/alber/PycharmProjects/EnviromentalVariables/.env")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")

@app.route('/')
def home():

    return render_template("index.html")


@app.route('/assign-asset')
def assign_asset():

    return render_template("assign_asset.html")


@app.route('/move-group')
def move_group():

    return render_template("assetgroup.html")


@app.route('/maintenance-event')
def maintenance_event():

    return render_template("createmaintenance.html")


@app.route('/maintenance-history')
def maintenance_history():

    return render_template("maintenancehistory.html")


@app.route('/new-asset')
def new_asset():

    return render_template("createasset.html")


@app.route('/new-assetgroup')
def new_assetgroup():

    return render_template("creategroup.html")


@app.route('/delet-data')
def delete_data():

    return render_template("deletedata.html")

if __name__ == "__main__":
    app.run(debug=True)