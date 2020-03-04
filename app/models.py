# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from app         import db
from flask_login import UserMixin

class User(UserMixin, db.Model):

    id       = db.Column(db.Integer,     primary_key=True)
    user     = db.Column(db.String(64),  unique = True)
    email    = db.Column(db.String(120), unique = True)
    password = db.Column(db.String(500))

    def __init__(self, user, email, password):
        self.user       = user
        self.password   = password
        self.email      = email

    def __repr__(self):
        return str(self.id) + ' - ' + str(self.user)

    def save(self):

        # inject self into db session    
        db.session.add ( self )

        # commit change and save the object
        db.session.commit( )

        return self 

class DeploymentLatest(db.Model):
    __tablename__ = 'deploymentlatest'
    app = db.Column(db.String(64), primary_key=True)
    image = db.Column(db.String(64))
    release = db.Column(db.String(64), unique=True)

    def __init__(self, app, image, release):
        self.app = app
        self.image = image
        self.release = release

    def __repr__(self):
        return self.app + ' - ' + self.image + ' - ' + self.release

    def save(self):
        # inject self into db session
        db.session.add(self)

        # commit change and save the object
        db.session.commit()

        return self