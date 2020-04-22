from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class UserRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Register')


class UserLoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class DocUploadForm(FlaskForm):
    files = MultipleFileField('Upload files', validators=[FileAllowed(['txt', 'pdf'])])
    submit = SubmitField('Upload')


class DomainForm(FlaskForm):
    name = StringField('Domain', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LabelUploadForm(FlaskForm):
    file = FileField('Upload Label Data in a CSV Format', validators=[FileAllowed(['csv'])])
    submit = SubmitField('Submit')



class ContextDistributionForm(FlaskForm):
    sentence = StringField('Sentence', validators=[Length(min=2, max=200)])
    submit = SubmitField('Submit')