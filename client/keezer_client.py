import os
import time
import json
import logging
import requests
import traceback
import time
import ConfigParser
import io
import threading
import RPi.GPIO as GPIO

# The primary sensor will be used for all sensor readings and determines
# whether we need to run the freezer.
# The secondary sensor will be used as a backup if the primary fails
# until the primary comes online again.
config_file = os.environ.get('KEEZER_CLIENT_SETTINGS')
if config_file is None:
	config_file = 'keezer_client.cfg'
with open(config_file, 'r') as f:
	config_text = f.read()
default_config = { 'secondary_temp': None, 'url': None, 'api_token': None, 'temperature': 40.0, 'deviation': 2.0, 'min_runtime': 60, 'cooldown': 300, 'fridge_name': 'fridgey' }
config = ConfigParser.SafeConfigParser(default_config, allow_no_value=True)
config.readfp(io.BytesIO(config_text))
primary_sensor_name = config.get('sensor', 'primary_temp')
secondary_sensor_name = config.get('sensor', 'secondary_temp')
relay_gpio_pin = config.getint('sensor', 'relay_pin')
server_url = config.get('server', 'url')
api_token = config.get('server', 'api_token')
desired_temperature = config.getfloat('fridge', 'temperature')
deviation = config.getfloat('fridge', 'deviation')
min_runtime = config.getint('fridge', 'min_runtime')
cooldown = config.getint('fridge', 'cooldown')
fridge_name = config.get('fridge', 'fridge_name')
max_temperature = desired_temperature + deviation

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='keezer_client.log',level=logging.ERROR,format=FORMAT)
logger = logging.getLogger('keezer_client')

def post_async(url, headers, data):
	try:
		requests.post(url, headers=headers, data=json.dumps(data))
	except Exception:
		# don't log these errors
		# it could fill up the log fast if the server goes down
		return
		

def post_exception(formatted_exception):
	if server_url is None or api_token is None:
		return
	url = server_url + 'api/error'
	headers = { 'Authorization': api_token, 'Content-Type': 'application/json' }
	data = { 'time': time.time(), 'error': formatted_exception }
	# fire and forget
	postErrorThread = threading.Thread(target=post_async, args=(url,headers,data))
	postErrorThread.start()

def post_reading(reading):
	if server_url is None or api_token is None:
		return
	url = server_url + 'api/reading'
	headers = { 'Authorization': api_token, 'Content-Type': 'application/json' }
	data = { 'time': reading.time, 'reading': reading.reading, 'sensorDescription': reading.sensor_name }
	postReadingThread = threading.Thread(target=post_async, args=(url,headers,data))
	postReadingThread.start()

class Reading():
	def __init__(self, sensor_name, reading, reading_time):
		self.sensor_name = sensor_name
		self.reading = reading
		self.time = reading_time

# Inherit from dictionary for easy JSON serialization.
class Sensor(dict):
	def __init__(self, name):
		self.file_name = '/sys/bus/w1/devices/' + name + '/w1_slave' 
		dict.__init__(self, name=name, file_name=self.file_name)
		self.name = name

	def get_reading(self):
		try:
			f = open(self.file_name, 'r')
			lines = f.readlines()
			reading_time = time.time()
			equals_pos = lines[1].find('t=')
			if equals_pos != -1:
				raw_temp = float(lines[1][equals_pos+2:])
				#murica
				temp_f = (raw_temp / 1000.0) * 9.0 / 5.0 + 32.0
				return Reading(self.name, temp_f, reading_time)
		except Exception:
			logger.exception('Error reading sensor value for {0}'.format(self.name))
			post_exception(traceback.format_exc())
		return None

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
primary_sensor = Sensor(primary_sensor_name)
secondary_sensor = None
if secondary_sensor_name is not None:
	secondary_sensor = Sensor(secondary_sensor_name)

try:
	# setup gpio pin for relay
	# we are using BCM numbering
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(relay_gpio_pin, GPIO.OUT)
	GPIO.output(relay_gpio_pin, False)

	# keep track of when the fridge was last turned on or off
	# we don't want to be turning it on/off frequently
	fridge_turned_on = 0
	fridge_turned_off = 0
	fridge_enabled = False
	while True:
		primary_reading = primary_sensor.get_reading()
		secondary_reading = None
		if secondary_sensor is not None:
			secondary_reading = secondary_sensor.get_reading()
			
		if primary_reading is not None:
			post_reading(primary_reading)
		if secondary_reading is not None:
			post_reading(secondary_reading)
		
		reading_to_use = primary_reading
		if reading_to_use is None:
			reading_to_use = secondary_reading
		if reading_to_use is None and fridge_enabled:
			GPIO.output(relay_gpio_pin, False)
			fridge_enabled = False
			fridge_turned_off = time.time()

		if reading_to_use is not None:
			if fridge_enabled:
				run_time = time.time() - fridge_turned_on
				if reading_to_use.reading < desired_temperature and run_time >= min_runtime:
					GPIO.output(relay_gpio_pin, False)
					fridge_enabled = False
					fridge_turned_off = time.time()
			else:
				time_since_last_ran = time.time() - fridge_turned_off
				if reading_to_use.reading > max_temperature and time_since_last_ran >= cooldown:
					GPIO.output(relay_gpio_pin, True)
					fridge_enabled = True
					fridge_turned_on = time.time()

		time.sleep(1)
except KeyboardInterrupt:
	GPIO.cleanup()
	exit(1)
except Exception:
	GPIO.cleanup()
	logger.exception('Fatal error in main loop')
	post_exception(traceback.format_exc())
