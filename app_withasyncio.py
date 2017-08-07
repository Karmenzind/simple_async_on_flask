#!/usr/bin/env python

import asyncio
import json
import os
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

engine = create_engine(user='root',
                       db='sakila',
                       host='127.0.0.1',
                       password=os.environ.get('PWD_OF_MYSQL', ''))


async def query(username):
    with (await engine) as conn:
        _sql = 'select * from users_for_flask where username = "%s"' % username
        res = await conn.execute(_sql)
        return res.fetchone()


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[Required(), Length(1, 64)])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Log In')


class AsyndbQuery(BaseQuery):
    '''Provide all kinds of query functions.'''

    def jsonify(self):
        '''Converted datas into JSON.'''
        for item in self.all():
            yield item.as_dict


class User(UserMixin, db.Model):
    query_class = AsyndbQuery

    __tablename__ = 'users_for_flask'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    @cached_property
    def as_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'password_hash': self.password_hash
        }

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

        db_data = await query(username)
        if db_data and check_password_hash(db_data[0]['password_hash'], password):
            print(1)
            return 'OK'
        print(2)
        return 'FAIL'
    return render_template('login.html', form=form)


async def init(loop):
    wsgi_flask_app = WSGIHandler(app)
    aio_app = web.Application(loop=loop)
    aio_app.router.add_route('*', '/{path_info:.*}', wsgi_flask_app)
    srv = await loop.create_server(aio_app.make_handler(), '127.0.0.1', 5000)
    return srv


if __name__ == '__main__':
    io_loop = asyncio.get_event_loop()
    io_loop.run_until_complete(init(io_loop))

    try:
        io_loop.run_forever()
    except KeyboardInterrupt:
        print('Interrupted')
