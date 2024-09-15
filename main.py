#________________________________________________flask libraries_______________________________________________________
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5

#_____________________________________________Project Libraries_________________________________________________________

from project_forms import AssignAsset, AssignAssetGroup, MaintenanceEvent, NewAsset, NewGroup, NewLocation
import os
from dotenv import load_dotenv

#________________________________________________sqlalchemy libraries__________________________________________________
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey

#_______________________________________________load enviroment variables_______________________________________________
load_dotenv("C:/Users/alber/PycharmProjects/EnviromentalVariables/.env")

#__________________________________________________initialize flask app_________________________________________________
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
Bootstrap5(app)

#______________________________________________create SQL database______________________________________________________
# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assets.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

#_______________________________________create tables in database______________________________________________________
#Create asset table
class Asset(db.Model):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sn: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str]= mapped_column(String(250), nullable=False)
    asset_group: Mapped[str]= mapped_column(String(250), nullable=False)
    description: Mapped[str]= mapped_column(String, nullable=False)
    location: Mapped[str]= mapped_column(String(250), nullable=False)
    district: Mapped[str]= mapped_column(String(250), nullable=False)
    op_status: Mapped[str]= mapped_column(String(250), nullable=False)

#Create table for all the asset groups
class AssetGroups(db.Model):
    __tablename__ = "assetgroups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]= mapped_column(String(250), nullable=False, unique=True)

class AssetLocations(db.Model):
    __tablename__ = "assetlocations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str]= mapped_column(String(250), nullable=False, unique=True)
    district: Mapped[str]= mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()

#_______________________________________Constants and variables_________________________________________________________

def get_group_list():
    with app.app_context():
        asset_gps = db.session.query(AssetGroups).all()

    ASSET_GROUP_LIST = []
    for element in asset_gps:
        ASSET_GROUP_LIST.append(element.name)

    return ASSET_GROUP_LIST

def get_locations():
    with app.app_context():
        asset_locations=db.session.query(AssetLocations).all()

    ASSET_LOCATIONS= []
    for element in asset_locations:
        ASSET_LOCATIONS.append(element.name)

    return ASSET_LOCATIONS

#______________________________________________flask functions routes___________________________________________________

@app.route('/')
def home():
    all_assets = db.session.query(Asset).all()
    return render_template("index.html", all_assets=all_assets)


@app.route('/assign-asset', methods=["GET", "POST"])
def assign_asset():
    all_assets = db.session.query(Asset).all()
    assign_asset_form = AssignAsset(group_choices=get_group_list(), location_choices=get_locations())
    if assign_asset_form.validate_on_submit():
        edit_asset= db.session.query(Asset).where(Asset.sn == assign_asset_form.sn.data).scalar()
        asset_location = db.session.query(AssetLocations).where(AssetLocations.name == assign_asset_form.location.data).scalar()
        if edit_asset:
            edit_asset.asset_group = assign_asset_form.asset_group.data
            edit_asset.location = assign_asset_form.location.data
            edit_asset.district = asset_location.district
            db.session.commit()
            print("asset was succesfully assign to a group")
            return redirect(url_for("home"))
        else:
            flash("Asset doesn't Exist, Check spelling")
    return render_template("assign_asset.html", form=assign_asset_form, all_assets=all_assets)


@app.route('/move-group', methods=["GET", "POST"])
def move_group():
    assign_group_form = AssignAssetGroup(group_choices=get_group_list(), location_choices=get_locations())
    if assign_group_form.validate_on_submit():
        assets_results= db.session.query(Asset).where(Asset.asset_group == assign_group_form.asset_group.data).all()
        asset_location= db.session.query(AssetLocations).where(AssetLocations.name == assign_group_form.asset_group_location.data).scalar()
        for asset in assets_results:
            asset.location= assign_group_form.asset_group_location.data
            asset.district= asset_location.district
            db.session.commit()
        print("asset group was successfully assign to a Location / District")
        return redirect(url_for("home"))
    return render_template("assetgroup.html", form=assign_group_form)


@app.route('/maintenance-event', methods=["GET", "POST"])
def maintenance_event():
    maintenance_event_form = MaintenanceEvent()
    if maintenance_event_form.validate_on_submit():
        print("maintenance event was created successfully")
    return render_template("createmaintenance.html", form=maintenance_event_form)


@app.route('/maintenance-history')
def maintenance_history():

    return render_template("maintenancehistory.html")


@app.route('/new-asset', methods=["GET", "POST"])
def new_asset():
    new_asset_form = NewAsset(group_choices=get_group_list(), location_choices=get_locations())
    if new_asset_form.validate_on_submit():
        old_asset =db.session.query(Asset).where(Asset.sn == new_asset_form.sn.data).scalar()
        asset_location= db.session.query(AssetLocations).where(AssetLocations.name == new_asset_form.asset_group_location.data).scalar()
        if old_asset:
            flash(f"The asset {new_asset_form.sn.data} already exist")

        else:
            new_asset_element = Asset(sn=new_asset_form.sn.data,
                                      name=new_asset_form.name.data,
                                      asset_group=new_asset_form.asset_group.data,
                                      description=new_asset_form.description.data,
                                      location=new_asset_form.asset_group_location.data,
                                      district=asset_location.district,
                                      op_status=new_asset_form.op_status.data)
            db.session.add(new_asset_element)
            db.session.commit()
            print("New asset was created successfully")
            return redirect(url_for("home"))
    return render_template("createasset.html", form=new_asset_form)


@app.route('/new-assetgroup', methods=["GET", "POST"])
def new_assetgroup():
    new_assetgroup_form = NewGroup()
    if new_assetgroup_form.validate_on_submit():
        old_assetgroup = db.session.query(AssetGroups).where(AssetGroups.name == new_assetgroup_form.new_group.data).scalar()
        if old_assetgroup:
            flash("Asset Group Already Exist")
        else:
            new_group = AssetGroups(name=new_assetgroup_form.new_group.data)
            db.session.add(new_group)
            db.session.commit()
            print(f"New Asset group {new_assetgroup_form.new_group.data} was created successfully")
            return redirect(url_for("home"))
    return render_template("creategroup.html", form=new_assetgroup_form)


@app.route('/new-location', methods=["GET", "POST"])
def new_location():
    new_location_form = NewLocation()
    if new_location_form.validate_on_submit():
        old_location = db.session.query(AssetLocations).where(AssetLocations.name == new_location_form.new_location.data).scalar()
        if old_location:
            flash("Location Already Exists")
        else:
            new_asset_location = AssetLocations(name=new_location_form.new_location.data,
                                                district=new_location_form.district.data)
            db.session.add(new_asset_location)
            db.session.commit()
            print("New location was created successfully")
            return redirect(url_for("home"))
    return render_template("createlocation.html", form=new_location_form)


@app.route('/delet-data')
def delete_data():

    return render_template("deletedata.html")

if __name__ == "__main__":
    app.run(debug=True)