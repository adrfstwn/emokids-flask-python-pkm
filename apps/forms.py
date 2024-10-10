from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from apps.models import User
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    username_or_email = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

    def validate_username_or_email(self, username_or_email):
        user = User.query.filter((User.username == username_or_email.data) | (User.email == username_or_email.data)).first()
        if not user:
            raise ValidationError('Invalid username or email.')

    def validate_password(self, password):
        user = User.query.filter((User.username == self.username_or_email.data) | (User.email == self.username_or_email.data)).first()
        if user and not user.check_password(password.data):
            raise ValidationError('Incorrect password.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email is already registered. Please use a different email address.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    whatsapp_number = StringField('WhatsApp Number')
    address = StringField('Address')
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')

    def populate_obj(self, obj):
        """Update the fields of the given object with data from the form."""
        obj.username = self.username.data
        obj.email = self.email.data
        obj.whatsapp_number = self.whatsapp_number.data
        obj.address = self.address.data
