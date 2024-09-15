from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField
from wtforms.validators import DataRequired
from wtforms.widgets.core import TextArea

district_choices = ["Victoria", "Midland", "Pennsylvania"]
op_status_choices = ["Good", "Bad", "Warning"]

def AssignAsset(group_choices):
    class AssignAssetForm(FlaskForm):
        sn= StringField(label="SN", validators=[DataRequired()])
        asset_group= SelectField(label="Asset Group", choices=group_choices)
        submit = SubmitField("Assign Asset to Group")
    return AssignAssetForm()

def  AssignAssetGroup(group_choices, location_choices):
    class AssignAssetGroupForm(FlaskForm):
        asset_group= SelectField(label="Asset Group", choices=group_choices)
        asset_group_location = SelectField(label="Select Location", choices=location_choices)
        asset_group_district = SelectField(label="Select District",
                                           choices=district_choices)
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
        asset_group_district = SelectField(label="Select District",
                                           choices=district_choices)
        op_status = SelectField(label="Operational Status", choices=op_status_choices)
        submit = SubmitField("Save New Asset")
    return NewAssetForm()

class NewGroup(FlaskForm):
    new_group= StringField(label="Group Asset Name", validators=[DataRequired()])
    submit = SubmitField("Create Asset Group")

class NewLocation(FlaskForm):
    new_location= StringField(label="Location Name", validators=[DataRequired()])
    submit = SubmitField("Create Location")