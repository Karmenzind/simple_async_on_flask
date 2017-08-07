#!/usr/bin/env python

import asyncio
import json
import sys
import aiomysql
from aiohttp import web
from flask_bootstrap import Bootstrap
from flask import Flask, jsonify
from werkzeug.utils import cached_property
from flask_sqlalchemy import SQLAlchemy, BaseQuery
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from gevent.monkey import patch_all
from psycogreen.gevent import patch_psycopg
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, LoginManager
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import Required, Length
from aiohttp_wsgi import WSGIHandler
from aiomysql.sa import create_engine

patch_all()
patch_psycopg()

app = Flask(__name__)
app.config.from_pyfile('config.py')

bootstrap = Bootstrap(app)
login_manager = LoginManager(app)

db = SQLAlchemy(app)
db.engine.pool._use_threadlocal = True


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Log In')


class User(UserMixin, db.Model):
    __tablename__ = 'users_for_flask'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
async def login():
    form = LoginForm()
    if request.method == 'POST':
        post_data = {} if form.validate_on_submit() else json.loads(request.data.decode('ascii'))
        username = form.username.data if form.validate_on_submit() else post_data['username']
        password = form.password.data if form.validate_on_submit() else post_data['password']
        user = User.query.filter_by(username=username).first()
        if user is not None and user.verify_password(password):
            login_user(user)
            print(1)
            return 'OK'
        print(2)
        return 'FAIL'
    return render_template('login.html', form=form)


if __name__ == '__main__':
    from gevent.pywsgi import WSGIServer

    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
