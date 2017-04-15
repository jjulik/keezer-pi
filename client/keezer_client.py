import os
import time
import json
import logging
import requests
import traceback
import time
import ConfigParser
import io

# The primary sensor will be used for all sensor readings and determines
# whether we need to run the freezer.
# The secondary sensor will be used as a backup if the primary fails
# until the primary comes online again.
config_file = os.environ.get('KEEZER_CLIENT_SETTINGS')
if config_file is None:
	config_file = 'keezer_client.cfg'
with open(config_file, 'r') as f:
	config_text = f.read()
default_config = { 'secondary_temp': None, 'url': None, 'api_token': None }
config = ConfigParser.SafeConfigParser(default_config, allow_no_value=True)
config.readfp(io.BytesIO(config_text))
primary_sensor_name = config.get('sensor', 'primary_temp')
secondary_sensor_name = config.get('sensor', 'secondary_temp')
relay_gpio_pin = config.getint('sensor', 'relay_pin')
server_url = config.get('server', 'url')
api_token = config.get('server', 'api_token')

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='keezer_client.log',level=logging.ERROR,format=FORMAT)
logger = logging.getLogger('keezer_client')

def post_exception(formatted_exception):
	if server_url is None or api_token is None:
		return
	try:
		url = server_url + 'api/error'
		headers = { 'Authorization': api_token }
		payload = { 'date': time.asctime(time.localtime()), error: formatted_exception }
		requests.post(url, headers=headers, data=payload)
	except Exception:
		logger.exception('Error uploading error to server')

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
			equals_pos = lines[1].find('t=')
			if equals_pos != -1:
				raw_temp = float(lines[1][equals_pos+2:])
				#murica
				temp_f = (raw_temp / 1000.0) * 9.0 / 5.0 + 32.0
				return temp_f
		except Exception:
			logger.exception('Error reading sensor value for {0}'.format(self.name))
			post_exception(traceback.format_exc())
		return None

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
primary_sensor = Sensor(primary_sensor_name)
if secondary_sensor_name is not None:
	secondary_sensor = Sensor(secondary_sensor_name)

try:
	while True:
		primary_reading = primary_sensor.get_reading()
		if secondary_sensor is not None:
			secondary_reading = secondary_sensor.get_reading()
		
		
		time.sleep(1)
except KeyboardInterrupt:
	exit(1)
except Exception:
	logger.exception('Fatal error in main loop')
	post_exception(traceback.format_exc())
