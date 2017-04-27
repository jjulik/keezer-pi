import os
import sqlite3
import random
import string
import click
from flask import Flask
from flask import Flask, request, session, g, redirect, url_for, abort, Response, jsonify, render_template
from functools import wraps

app = Flask(__name__)

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'keezer_server.db'),
	DEBUG=False
))

app.config.from_envvar('KEEZER_SETTINGS', silent=True)

def auth_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		token = request.headers.get('Authorization',type=str)
		if token is None:
			resp = Response('Unauthorized', status=401)
			# try to be compliant with RFC 7235
			resp.headers.set('WWW-Authenticate', 'Bearer realm="{0}", title"Authorization token missing"'.format(request.headers['Host']))
			return resp
		db = get_db()
		queryResult = query_db('select active from token where active = 1 and token = ?',args=[token],one=True)
		if queryResult is None or queryResult['active'] is None:
			resp = Response('Invalid token', status=401)
			resp.headers.set('WWW-Authenticate', 'Bearer realm="{0}", title="Invalid Authorization token"'.format(request.headers['Host']))
			return resp
		return f(*args, **kwargs)
	return decorated_function

@app.route('/')
def hello_world():
	return render_template('index.html')

@app.route('/api/reading', methods=['POST'])
@auth_required
def post_reading():
	sensor_description = request.json['sensorDescription']
	reading = request.json['reading']
	reading_time = request.json['time']
	sensor_query = query_db('select sensorid from sensor where description = ?', [sensor_description], one=True)
	if sensor_query is None or sensor_query['sensorid'] is None:
		resp = Response('Invalid sensor description', status=400)
		return resp
	query_db('insert into reading (sensorid, value, [time]) values (?,?,?)', [sensor_query['sensorid'], reading, reading_time])
	return jsonify({'success': True})

@app.route('/api/error', methods=['POST'])
@auth_required
def post_error():
	error = request.json['error']
	error_time = request.json['time']
	query_db('insert into clienterror ([time], error) values (?,?)', [error_time, error])
	return jsonify({'success': True})

def init_db():
	"""Initializes the database."""
	db = get_db()
	with app.open_resource('schema.sql', mode='r') as f:
		db.cursor().executescript(f.read())
	db.commit()

@app.route('/api/sensors', methods=['GET'])
def api_get_sensors():
	sensors = get_sensors()
	sensor_list = []
	for s in sensors:
		sensor_list.append({'sensorid': s['sensorid'],'sensortype': s['sensortype'], 'description': s['description']})
	return jsonify(sensor_list)	

@app.route('/api/readings')
def api_get_readings():
	timelimit = request.args.get('timelimit', 300, type=int)
	sensorid = request.args.get('sensorid', type=int)
	print timelimit
	print sensorid
	query = query_db("select * from reading where sensorid = ? order by readingid desc limit 100", [sensorid])
	readings = []
	for r in query:
		readings.append({'readingid': r['readingid'], 'value': r['value'], 'time': r['time']})
	return jsonify(readings)
	

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
	return query_db('select token from token')

@app.cli.command('gettokens')
def gettokens():
	"""Lists all the active tokens."""
	tokens = get_tokens()
	print('Tokens:')
	for t in tokens:
		print('%s' % t['token'])

def add_sensor(description, sensortype):
	"""Creates a new sensor."""
	db = get_db()
	query_db('insert into sensor (description, sensortype) values (?, ?)', [description, sensortype])
	return query_db('select last_insert_rowid() as sensorid', [], True)
	

@app.cli.command('addsensor')
@click.argument('description')
@click.argument('sensortype')
def addsensor(description, sensortype):
	"""Adds a sensor"""
	sensor = add_sensor(description, sensortype)
	print('Added sensor id: %d' % sensor['sensorid'])

def get_sensors():
	""" Gets all the sensors in the database."""
	db = get_db()
	return query_db('select sensorid, sensortype, description from sensor')

@app.cli.command('getsensors')
def getsensors():
	"""Lists all the sensors."""
	sensors = get_sensors()
	print('Sensors:')
	for s in sensors:
		print('{0}    {1}    {2}'.format(s['sensorid'], s['sensortype'], s['description']))

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

