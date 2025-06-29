
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length


district_choices = ["Victoria", "Midland", "Pennsylvania"]
op_status_choices = ["Good", "Bad", "Warning"]

def AssignAsset(group_choices, location_choices):
    class AssignAssetForm(FlaskForm):
        sn= StringField(label="SN", validators=[DataRequired()])
        asset_group= SelectField(label="Asset Group", choices=group_choices)
        location= SelectField(label= "Select Location", choices= location_choices)
        submit = SubmitField("Assign Asset to Group / Location")
    return AssignAssetForm()

def  AssignAssetGroup(group_choices, location_choices):
    class AssignAssetGroupForm(FlaskForm):
        asset_group= SelectField(label="Asset Group", choices=group_choices)
        asset_group_location = SelectField(label="Select Location", choices=location_choices)
        submit = SubmitField("Assign Asset Group")
    return AssignAssetGroupForm()

class MaintenanceEvent(FlaskForm):
    sn= StringField(label="SN", validators=[DataRequired()])
    description = TextAreaField(label="Description",render_kw={"rows": 5}, validators=[DataRequired()])
    op_status= SelectField(label="Operational Status", choices=op_status_choices)
    submit = SubmitField("Create Event")

def NewAsset(group_choices, location_choices):
    class NewAssetForm(FlaskForm):
        sn= StringField(label="SN", validators=[DataRequired()])
        name = StringField(label="Name", validators=[DataRequired()])
        asset_group= SelectField(label="Asset Group", choices=group_choices)
        description = StringField(label="Description", validators=[DataRequired()])
        asset_group_location = SelectField(label="Select Location", choices=location_choices)
        op_status = SelectField(label="Operational Status", choices=op_status_choices)
        submit = SubmitField("Save Asset")
    return NewAssetForm()

class NewGroup(FlaskForm):
    new_group= StringField(label="Group Asset Name", validators=[DataRequired()])
    submit = SubmitField("Create Asset Group")

class NewLocation(FlaskForm):
    new_location= StringField(label="Location Name", validators=[DataRequired()])
    district= SelectField(label="Select District", choices=district_choices)
    submit = SubmitField("Create Location")

class DeleteDataAsset(FlaskForm):
    asset_sn = StringField(label="Input Asset SN to delete:")
    submit = SubmitField("Delete Asset")

def DeleteDataGroup(group_choices):
    class DeleteAssetGroup(FlaskForm):
        asset_groups=SelectField(label="Choose Asset Group:", choices=group_choices)
        submit = SubmitField("Delete Asset Group")
    return DeleteAssetGroup()

def DeleteDataLocation(location_choices):
    class DeleteAssetLocation(FlaskForm):
        field_locations = SelectField(label="Choose Field Location:", choices=location_choices)
        submit = SubmitField("Delete Field Location")
    return DeleteAssetLocation()

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    is_admin = BooleanField('Admin')
    submit = SubmitField('Register User')

class RepairForm(FlaskForm):
    repair_description = StringField("Repair Description", validators=[DataRequired()])
    submit = SubmitField("Submit Repair")