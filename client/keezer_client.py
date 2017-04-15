import os
import time
import json
import logging

# The primary sensor will be used for all sensor readings and determines
# whether we need to run the freezer.
# The secondary sensor will be used as a backup if the primary fails
# until the primary comes online again.
primary_sensor_name = '28-0416717fbfff'
secondary_sensor_name = '28-051670fd64ff'
relay_gpio_pin = 1
server_url = None
api_token = None

# by default, log to /var/log/keezer_client.log
FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(filename='keezer_client.log',level=logging.ERROR,format=FORMAT)
logger = logging.getLogger('keezer_client')

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
			# log error to server
			#if server_url is not None:
				# do stuff
			logger.exception('Error reading sensor value for {0}'.format(self.name))
		return None

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
primary_sensor = Sensor(primary_sensor_name)
secondary_sensor = Sensor(secondary_sensor_name)

try:
	while True:
		primary_reading = primary_sensor.get_reading()
		secondary_reading = secondary_sensor.get_reading()
		
		
		time.sleep(1)
except Exception:
	logger.exception('Fatal error in main loop')
