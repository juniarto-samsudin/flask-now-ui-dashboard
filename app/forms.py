# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask_wtf          import FlaskForm
from flask_wtf.file     import FileField, FileRequired
from wtforms            import StringField, TextAreaField, SubmitField, PasswordField, SelectField
from wtforms.validators import InputRequired, Email, DataRequired

class LoginForm(FlaskForm):
	username    = StringField  (u'Username'        , validators=[DataRequired()])
	password    = PasswordField(u'Password'        , validators=[DataRequired()])

class RegisterForm(FlaskForm):
	name        = StringField  (u'Name'      )
	username    = StringField  (u'Username'  , validators=[DataRequired()])
	password    = PasswordField(u'Password'  , validators=[DataRequired()])
	email       = StringField  (u'Email'     , validators=[DataRequired(), Email()])

class DeployAppForm(FlaskForm):
	application = SelectField   (u'Application', choices=[('cpp','C++')])
	image		= SelectField	(u'Image', choices=[('test','Test')])

class QueryDevEnvVarsForm(FlaskForm):
	device = SelectField (u'Device', choices=[('cpp','C++')])

class SetDevEnvVarsForm(FlaskForm):
	device = SelectField(u'Device', choices=[('cpp','C++')])
	envvar = StringField(u'Envvar', validators=[DataRequired()])
	value = StringField(u'value', validators=[DataRequired()])