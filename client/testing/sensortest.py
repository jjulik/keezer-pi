import os
import glob
import time
import json

class Sensor(dict):
	def __init__(self, name):
		self.readings = {}
		dict.__init__(self, name=name, readings=self.readings)
		self.name = name

	def add_reading(self, loopcount):
		f = open(self.name, 'r')
		lines = f.readlines()
		equals_pos = lines[1].find('t=')
		if equals_pos != -1:
			raw_temp = float(lines[1][equals_pos+2:])
			self.readings[loopcount] = raw_temp

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')
base_dir = '/sys/bus/w1/devices/'
device_folders = glob.glob(base_dir + '28*')
sensors = []
for device_folder in device_folders:
	sensors.append(Sensor(device_folder + '/w1_slave'))

try:
	loopcount = 0
	while True:
		for s in sensors:
			s.add_reading(loopcount)
		time.sleep(1)
		loopcount = loopcount + 1
except KeyboardInterrupt:
	print(json.dumps({'sensors': sensors}))
