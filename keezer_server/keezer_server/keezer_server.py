import os
import sqlite3
import random
import string
from flask import Flask
from flask import Flask, request, session, g, redirect, url_for, abort

app = Flask(__name__)

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'keezer_server.db'),
	DEBUG=False
))

app.config.from_envvar('KEEZER_SETTINGS', silent=True)

@app.route('/')
def hello_world():
	return 'Hello, World!'

def init_db():
	"""Initializes the database."""
	db = get_db()
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	init_db()
	print('Initialized the database.')

def query_db(query, args=(), one=False):
	db = get_db()
	cur = db.execute(query, args)
	rv = cur.fetchall()
	cur.close()
	db.commit()
	return (rv[0] if rv else None) if one else rv

def add_token():
	"""Creates and returns a new token."""
	db = get_db()
	token = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(64))
	query_db('insert into token (token, active) values (?, 1)', [token])
	return token

@app.cli.command('addtoken')
def addtoken():
	"""Adds an API Token"""
	token = add_token()
	print('Added token: %s' % token)

def get_tokens():
	""" Get all the active tokens in the datbase."""
	db = get_db()
	return query_db('select token from token')

@app.cli.command('gettokens')
def gettokens():
	"""Lists all the active tokens."""
	tokens = get_tokens()
	print('Tokens:')
	for t in tokens:
		print('%s' % t['token'])

def connect_db():
	"""Connects to the sqlite database specified in the config"""
	db = sqlite3.connect(app.config['DATABASE'])
	db.row_factory = sqlite3.Row
	return db

def get_db():
	"""Opens a new database connection if there is noe yet for the current
	application context."""
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = connect_db()
	return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
	"""Closes the database again at the end of the request."""
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()

