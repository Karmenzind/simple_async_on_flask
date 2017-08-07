#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:%s@localhost/sakila' % os.environ.get('PWD_OF_MYSQL', '')
SQLALCHEMY_ECHO = False
SQLALCHEMY_POOL_SIZE = 10
SECRET_KEY = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
DEBUG = True
