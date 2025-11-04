#________________________________________________flask libraries_______________________________________________________
from flask import Flask, render_template, redirect, url_for, flash, abort, request, Response, send_file
from flask_bootstrap import Bootstrap5
from flask_migrate import Migrate

#_____________________________________________Project Libraries_________________________________________________________

from project_forms import AssignAsset, AssignAssetGroup, MaintenanceEvent, NewAsset, NewGroup, NewLocation, DeleteDataAsset, DeleteDataGroup, DeleteDataLocation, LoginForm, RegisterUserForm, RepairForm

from functools import wraps

import os
import mimetypes
from io import BytesIO

from datetime import datetime, timedelta, date

from typing import Optional


#________________________________________________sqlalchemy libraries__________________________________________________
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ForeignKey, LargeBinary, Date

#_______________________________________________load enviroment variables_______________________________________________
import config
from connection import get_connection

#________________________________________________ werkzeug libraries____________________________________________________
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

#__________________________________________________initialize flask app_________________________________________________
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 megabytes
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
Bootstrap5(app)

#________________________________________________Initialize LoginManager________________________________________________
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # redirect to this view if not logged in

#______________________________________________create SQL database______________________________________________________
# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{config.DB_USER}:{config.DB_PASSWORD}@{config.DB_HOST}/{config.DB_NAME_ASSETMANAGER}'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

migrate = Migrate(app, db)

#_______________________________________create tables in database______________________________________________________
#Create asset table
class Asset(db.Model):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sn: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    name: Mapped[str]= mapped_column(String(250), nullable=False)
    asset_group: Mapped[str]= mapped_column(String(250), nullable=False)
    description: Mapped[str]= mapped_column(String(250), nullable=False)
    location: Mapped[str]= mapped_column(String(250), nullable=False)
    district: Mapped[str]= mapped_column(String(250), nullable=False)
    op_status: Mapped[str]= mapped_column(String(250), nullable=False)

    file_data: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    file_extension: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    expiration_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    maintenance= relationship("Maintenance", back_populates="parent_asset")

class Maintenance(db.Model):
    __tablename__= "maintenance"
    id: Mapped[int]= mapped_column(Integer, primary_key=True)
    sn: Mapped[str]= mapped_column(String(250), nullable=False)
    name: Mapped[str]= mapped_column(String(250), nullable=False)
    date: Mapped[str]= mapped_column(String(250), nullable=False)
    event_description: Mapped[str]= mapped_column(String(250), nullable=False)
    user: Mapped[str]= mapped_column(String(250), nullable=False)
    op_status: Mapped[str]= mapped_column(String(250), nullable=False)

    asset_id: Mapped[int] =mapped_column(Integer, db.ForeignKey("assets.id"))
    parent_asset= relationship("Asset", back_populates="maintenance")

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

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)  # store hashed passwords
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


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

def update_asset_status(asset_sn):
    # Get all maintenance events for this asset
    events = db.session.query(Maintenance).filter_by(sn=asset_sn).all()

    # Determine new status based on rules
    status = "Good"  # default

    for event in events:
        if event.op_status.lower() == "bad":
            status = "Bad"
            break  # highest priority, stop checking
        elif event.op_status.lower() == "warning":
            status = "Warning"
            # don't break — might still find a "bad" status

    # Update the asset's operational status
    asset = db.session.query(Asset).filter_by(sn=asset_sn).first()
    if asset:
        asset.op_status = status
        db.session.commit()

def check_expirations():
    with app.app_context():
        today = date.today()
        one_month_later = today + timedelta(days=30)

        assets = Asset.query.filter(Asset.expiration_date != None).all()

        for asset in assets:
            exp_date = asset.expiration_date
            if not exp_date:
                continue

            # Fetch all maintenance events related to expiration
            events = Maintenance.query.filter_by(parent_asset=asset).all()

            has_bad_event = None
            has_warning_event = None

            for e in events:
                desc = e.event_description.lower()
                status = e.op_status.lower()
                if "expired" in desc and status == "bad":
                    has_bad_event = e
                elif "about to expire" in desc and status == "warning":
                    has_warning_event = e

            # ✅ CASE 1: Asset expiration date now GOOD — remove warning/bad
            if exp_date > one_month_later:
                for event in [has_bad_event, has_warning_event]:
                    if event:
                        event.op_status = "Repaired"
                        event.event_description = "Asset expiration resolved"
                        event.date = today.strftime('%Y-%m-%d')
                        event.user = "System"
                        db.session.add(event)
                        db.session.commit()
                        update_asset_status(asset.sn)
                continue  # Skip rest since asset is no longer close to expiring

            # ✅ CASE 2: Expired asset → create "bad" event (only if not exists)
            if exp_date < today:
                if not has_bad_event:
                    new_maintenance_event = Maintenance(
                        sn=asset.sn,
                        name=asset.name,
                        date=today.strftime('%Y-%m-%d'),
                        event_description="Asset is expired",
                        user="System",
                        op_status="Bad",
                        parent_asset=asset
                    )
                    db.session.add(new_maintenance_event)
                    db.session.commit()
                    update_asset_status(asset.sn)

            # ✅ CASE 3: Asset expiring soon → create "warning" event
            elif today <= exp_date <= one_month_later:
                if not has_warning_event:
                    new_maintenance_event = Maintenance(
                        sn=asset.sn,
                        name=asset.name,
                        date=today.strftime('%Y-%m-%d'),
                        event_description="Asset is about to expire",
                        user="System",
                        op_status="Warning",
                        parent_asset=asset
                    )
                    db.session.add(new_maintenance_event)
                    db.session.commit()
                    update_asset_status(asset.sn)

        print(f"Asset expiration check completed. at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

#____________________________________admin_required decorator__________________________________________________________
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403

#______________________________________________flask functions routes___________________________________________________

@app.route('/')
def home():
    all_assets = db.session.query(Asset).all()
    return render_template("index.html", all_assets=all_assets)


@app.route('/assign-asset', methods=["GET", "POST"])
@login_required
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
            flash('asset was succesfully assign to a group', 'success')
            return redirect(url_for("home"))
        else:
            flash("Asset doesn't Exist, Check spelling", "danger")
    return render_template("assign_asset.html", form=assign_asset_form, all_assets=all_assets)


@app.route('/move-group', methods=["GET", "POST"])
@login_required
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
        flash(f'asset {assign_group_form.asset_group.data} group was successfully assign to a Location / District', 'success')
        return redirect(url_for("home"))
    return render_template("assetgroup.html", form=assign_group_form)


@app.route('/maintenance-event', methods=["GET", "POST"])
@login_required
def maintenance_event():

    sn_prefill = request.args.get('sn')

    maintenance_event_form = MaintenanceEvent()

    # Prefill SN field if passed from asset detail page
    if sn_prefill:
        maintenance_event_form.sn.data = sn_prefill

    if maintenance_event_form.validate_on_submit():
        asset_maintenance = db.session.query(Asset).where(Asset.sn == maintenance_event_form.sn.data).scalar()
        if asset_maintenance:
            new_maintenance_event= Maintenance(sn=maintenance_event_form.sn.data,
                                                   name=asset_maintenance.name,
                                                   date=date.today().strftime('%Y-%m-%d'),
                                                   event_description=maintenance_event_form.description.data,
                                                   user=current_user.username,
                                                   op_status=maintenance_event_form.op_status.data,
                                                   parent_asset=asset_maintenance)
            db.session.add(new_maintenance_event)
            db.session.commit()

            update_asset_status(asset_sn=maintenance_event_form.sn.data)
            flash("Maintenance event created successfully!", "success")
            return redirect(url_for('maintenance_history', sn= sn_prefill))

        else:
            flash("Asset doesn't exist, Please create New Asset", "danger")
    return render_template("createmaintenance.html", form=maintenance_event_form)


@app.route('/maintenance-history', methods=['GET', 'POST'])
def maintenance_history():
    sn_filter = request.args.get('sn') or request.form.get('sn')
    query = db.session.query(Maintenance)

    if sn_filter:
        query = query.filter_by(sn=sn_filter)

    maintenance_records = query.all()
    return render_template('maintenancehistory.html', records=maintenance_records)


@app.route('/new-asset', methods=["GET", "POST"])
@login_required
def new_asset():
    new_asset_form = NewAsset(group_choices=get_group_list(), location_choices=get_locations())
    if new_asset_form.validate_on_submit():
        old_asset =db.session.query(Asset).where(Asset.sn == new_asset_form.sn.data).scalar()
        asset_location= db.session.query(AssetLocations).where(AssetLocations.name == new_asset_form.asset_group_location.data).scalar()
        if old_asset:
            flash(f"The asset {new_asset_form.sn.data} already exist", "danger")

        else:
            new_asset_element = Asset(sn=new_asset_form.sn.data,
                                      name=new_asset_form.name.data,
                                      asset_group=new_asset_form.asset_group.data,
                                      description=new_asset_form.description.data,
                                      location=new_asset_form.asset_group_location.data,
                                      district=asset_location.district,
                                      op_status=new_asset_form.op_status.data,
                                      expiration_date=new_asset_form.expiration_date.data,)

            uploaded_file = new_asset_form.file_data.data
            if uploaded_file:
                # Get file extension
                filename = secure_filename(uploaded_file.filename)
                file_ext = os.path.splitext(filename)[1]  # e.g., '.pdf', '.jpg'

                # Store binary + extension
                new_asset_element.file_data = uploaded_file.read()
                new_asset_element.file_extension = file_ext.lower()  # Save in lowercase for consistency

            db.session.add(new_asset_element)
            db.session.commit()

            check_expirations()

            flash(f'Asset {new_asset_form.sn.data} was Created successfully', 'success')
            return redirect(url_for("home"))
    return render_template("createasset.html", form=new_asset_form)


@app.route('/new-assetgroup', methods=["GET", "POST"])
@login_required
@admin_required
def new_assetgroup():
    new_assetgroup_form = NewGroup()
    if new_assetgroup_form.validate_on_submit():
        old_assetgroup = db.session.query(AssetGroups).where(AssetGroups.name == new_assetgroup_form.new_group.data).scalar()
        if old_assetgroup:
            flash(f"Asset Group {new_assetgroup_form.new_group.data} Already Exist", "danger")
        else:
            new_group = AssetGroups(name=new_assetgroup_form.new_group.data)
            db.session.add(new_group)
            db.session.commit()
            print(f"New Asset group {new_assetgroup_form.new_group.data} was created successfully")
            flash(f"Asset Group {new_assetgroup_form.new_group.data} was created successfully", "success")
            return redirect(url_for("home"))
    return render_template("creategroup.html", form=new_assetgroup_form)


@app.route('/new-location', methods=["GET", "POST"])
@login_required
@admin_required
def new_location():
    new_location_form = NewLocation()
    if new_location_form.validate_on_submit():
        old_location = db.session.query(AssetLocations).where(AssetLocations.name == new_location_form.new_location.data).scalar()
        if old_location:
            flash(f"Location {new_location_form.new_location.data} Already Exists", "danger")
        else:
            new_asset_location = AssetLocations(name=new_location_form.new_location.data,
                                                district=new_location_form.district.data)
            db.session.add(new_asset_location)
            db.session.commit()
            print("New location was created successfully")
            flash(f"Location {new_location_form.new_location.data} was created successfully", "success")
            return redirect(url_for("home"))
    return render_template("createlocation.html", form=new_location_form)


@app.route("/asset/<sn>/delete", methods=["POST"])
@login_required
@admin_required
def delete_asset(sn):
    asset = db.session.query(Asset).filter_by(sn=sn).first()
    if not asset:
        return "Asset not found", 404

    #delete related maintenance records first
    db.session.query(Maintenance).filter_by(sn=sn).delete()

    db.session.delete(asset)
    db.session.commit()
    flash(f'Asset {asset.sn} deleted successfully.', "success")

    return redirect(url_for("home"))

@app.route('/delete-group', methods=["GET", "POST"])
@login_required
@admin_required
def delete_group():
    delete_group_form= DeleteDataGroup(group_choices=get_group_list())

    if delete_group_form.validate_on_submit():
        group_to_delete= db.session.query(AssetGroups).where(AssetGroups.name == delete_group_form.asset_groups.data).scalar()

        if group_to_delete:
            db.session.delete(group_to_delete)
            db.session.commit()
            flash(f"Group {delete_group_form.asset_groups.data} has been deleted successfully", "success")
        else:
            flash("Select a group to delete", "danger")

    return render_template("deletegroup.html", form=delete_group_form)

@app.route('/delete-location', methods=["GET", "POST"])
@login_required
@admin_required
def delete_location():
    delete_location_form= DeleteDataLocation(location_choices=get_locations())

    if delete_location_form.validate_on_submit():
        location_to_delete= db.session.query(AssetLocations).where(AssetLocations.name == delete_location_form.field_locations.data).scalar()

        if location_to_delete:
            db.session.delete(location_to_delete)
            db.session.commit()
            flash(f"Location {delete_location_form.field_locations.data} has been deleted successfully", "success")
        else:
            flash("Select a Field Location to Delete", "danger")

    return render_template("deletelocation.html", form=delete_location_form)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html", form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

@app.route('/register-user', methods=['GET', 'POST'])
@login_required
def register_user():
    if not current_user.is_admin:
        flash("Unauthorized access", "danger")
        return redirect(url_for('index'))

    form = RegisterUserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Username already exists", "warning")
        else:
            new_user = User(username=form.username.data, is_admin=form.is_admin.data)
            new_user.set_password(form.password.data)
            db.session.add(new_user)
            db.session.commit()
            flash("User registered successfully", "success")
            return redirect(url_for('register_user'))

    return render_template('register_user.html', form=form)


@app.route("/asset/<sn>")
@login_required
def asset_detail(sn):
    asset = db.session.query(Asset).filter_by(sn=sn).first()
    if not asset:
        return "Asset not found", 404
    return render_template("asset_detail.html", asset=asset)


@app.route("/asset/<sn>/edit", methods=["GET", "POST"])
@login_required
def edit_asset(sn):

    asset_selected = db.session.query(Asset).filter_by(sn=sn).first()
    if not asset_selected:
        return "Asset not found", 404


    edit_asset_form=NewAsset(group_choices=get_group_list(), location_choices=get_locations())

    # Update existing asset using form data

    if edit_asset_form.validate_on_submit():
        original_asset_sn= asset_selected.sn #saving the original value of the sn to update the maintenance table

        asset_selected.sn= edit_asset_form.sn.data
        asset_selected.name= edit_asset_form.name.data
        asset_selected.description= edit_asset_form.description.data
        asset_selected.asset_group= edit_asset_form.asset_group.data
        asset_selected.location= edit_asset_form.asset_group_location.data
        #asset_selected.op_status = edit_asset_form.op_status.data # This is omited since user needs to create a maintenance event instead

        asset_location = db.session.query(AssetLocations).where(
            AssetLocations.name == edit_asset_form.asset_group_location.data).scalar()

        asset_selected.district= asset_location.district

        asset_selected.expiration_date = edit_asset_form.expiration_date.data

        uploaded_file = edit_asset_form.file_data.data

        if uploaded_file:
            # Get file extension
            filename = secure_filename(uploaded_file.filename)
            file_ext = os.path.splitext(filename)[1]  # e.g., '.pdf', '.jpg'

            # Store binary + extension
            asset_selected.file_data = uploaded_file.read()
            asset_selected.file_extension = file_ext.lower()  # Save in lowercase for consistency



        if original_asset_sn != edit_asset_form.sn.data:
            db.session.query(Maintenance).filter_by(sn=original_asset_sn).update({"sn": edit_asset_form.sn.data})

        db.session.commit()
        check_expirations()

        flash(f'Asset {edit_asset_form.sn.data} was edited successfully', 'success')
        return redirect(url_for("asset_detail", sn=asset_selected.sn))



    # Pre-fill form data from the asset object

    edit_asset_form.sn.data= asset_selected.sn
    edit_asset_form.name.data= asset_selected.name
    edit_asset_form.description.data = asset_selected.description
    edit_asset_form.op_status.data = asset_selected.op_status
    if asset_selected.asset_group in get_group_list():
        edit_asset_form.asset_group.data= asset_selected.asset_group
    if asset_selected.location in get_locations():
        edit_asset_form.asset_group_location.data= asset_selected.location
    edit_asset_form.expiration_date.data = asset_selected.expiration_date

    return render_template("edit_asset.html", form=edit_asset_form)


@app.route('/repair-asset/<int:event_id>', methods=['GET', 'POST'])
@login_required
def repair_asset(event_id):
    event = db.session.query(Maintenance).get(event_id)

    if not event:
        flash("Maintenance event not found.", "danger")
        return redirect(url_for("maintenance_history"))

    form = RepairForm()

    if form.validate_on_submit():
        # Append to the event description
        repair_date = date.today().strftime('%Y-%m-%d')
        repair_user= current_user.username
        event.event_description += f"\n{repair_date} by {repair_user}\nRepair: {form.repair_description.data}"
        # Update the status
        event.op_status = "Repaired"
        db.session.commit()
        update_asset_status(asset_sn=event.sn)
        flash("Maintenance event updated successfully.", "success")
        return redirect(url_for("maintenance_history", sn=event.sn))

    return render_template("repair_asset.html", form=form, event=event)

@app.route('/repair-asset-redirect', methods=['GET'])
@login_required
def repair_asset_redirect():
    event_id = request.args.get('event_id', type=int)
    if event_id:
        return redirect(url_for('repair_asset', event_id=event_id))
    flash("Please select a maintenance event first.", "warning")
    return redirect(url_for('maintenance_history'))

@app.template_filter('nl2br')
def nl2br(value):
    return value.replace('\n', '<br>')

@app.route('/assets/<int:asset_id>/download')
def download_asset_file(asset_id):
    asset = Asset.query.get_or_404(asset_id)

    if not asset.file_data:
        flash("No file uploaded for this asset.", "warning")
        return redirect(url_for('asset_detail', id=asset.id))

    # Determine file extension and build filename
    extension = asset.file_extension or ''
    filename = f"asset_file_{asset.sn}{extension}"

    # Guess MIME type from extension
    mime_type, _ = mimetypes.guess_type(filename)
    mime_type = mime_type or 'application/octet-stream'

    return send_file(
        BytesIO(asset.file_data),
        as_attachment=True,
        download_name=filename,
        mimetype=mime_type
    )

@app.route("/job_streaming", methods=['GET', 'POST'])
@login_required
def active_job_streaming():

    return render_template("job_streaming.html")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=80)