from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.utils import timezone_choices

from .models import User


class LoginForm(FlaskForm):
    #username = StringField(u'Username', validators=[DataRequired()])
    email = StringField(u'Email', validators=[DataRequired(), Email(), Length(min=6, max=50)])
    password = PasswordField(u'Password', validators=[DataRequired()])

    def validate(self):
        check_validate = super(LoginForm, self).validate()

        # if our validators do not pass
        if not check_validate:
            return False

        # Does the user exist
        user = User.query.filter_by(email=self.email.data).first()
        if not user:
            self.email.errors.append('Invalid username or password')
            return False

        # Do the passwords match
        if not user.check_password(self.password.data):
            self.email.errors.append('Invalid username or password')
            return False

        return True


class RegisterForm(FlaskForm):
    """Register form."""

    email = StringField(u'Email', validators=[DataRequired(), Email(), Length(min=6, max=50)])
    username = StringField(u'Username', validators=[DataRequired(), Length(min=6, max=25)])
    firstname = StringField(u'First Name', validators=[DataRequired(), Length(min=2, max=30)])
    lastname = StringField(u'Last Name', validators=[DataRequired(), Length(min=2, max=30)])
    jobtitle = StringField(u'Job Title', validators=[DataRequired(), Length(min=2, max=30)])
    password = PasswordField(u'Password', validators=[DataRequired(), Length(min=6, max=40)])
    confirm = PasswordField(u'Verify password', [DataRequired(), EqualTo('password', message='Passwords must match')])

    # def __init__(self, *args, **kwargs):
    #     """Create instance."""
    #     super(RegisterForm, self).__init__(*args, **kwargs)
    #     self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(RegisterForm, self).validate()
        if not initial_validation:
            return False
        user = User.query.filter_by(email=self.email.data).first()
        if user:
            self.email.errors.append('Email already registered')
            return False
        user = User.query.filter_by(username=self.username.data).first()
        if user:
            self.username.errors.append('Username already registered')
            return False
        return True


class NewProjectForm(FlaskForm):
    """New Project form."""

    name = StringField('Project Name', validators=[DataRequired(), Length(min=3, max=60)])
    company = StringField('Company', validators=[Length(min=0, max=60)])
    address = StringField('Address', validators=[Length(min=0, max=60)])
    city = StringField('City', validators=[Length(min=0, max=40)])
    state = StringField('State', validators=[Length(min=0, max=30)])
    zipcode = StringField('Zip Code', validators=[Length(min=0, max=5)])
    country = StringField('Country', validators=[Length(min=0, max=30)])
    timezone = SelectField('Time Zone', choices=timezone_choices(), validators=[DataRequired()])
    description = StringField('Description', validators=[Length(min=0, max=120)])
    location = StringField('Location', validators=[Length(min=0, max=60)])

    # def __init__(self, *args, **kwargs):
    #     """Create instance."""
    #     super(RegisterForm, self).__init__(*args, **kwargs)
    #     self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(NewProjectForm, self).validate()
        if not initial_validation:
            return False

        return True
