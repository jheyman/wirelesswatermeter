#!/usr/bin/python
# -*- coding: utf-8 -*-
# Credits to python port of nrf24l01, Joao Paulo Barrac & maniacbugs original c library, and this blog: http://blog.riyas.org

from nrf24 import NRF24
import time
import os
import logging
import logging.handlers
import sys
import unicodedata
import pytz
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from ConfigParser import SafeConfigParser
from apscheduler.schedulers.background import BackgroundScheduler

import urllib
import urllib2

remote_log_url = 'http://192.168.0.13:8081/graphlist_insert.php'
def remoteLog(valueToLog):
	
	values = {'dataId' : 'waterMeter' }
	values['value'] = str(valueToLog)

	data = urllib.urlencode(values)
	req = urllib2.Request(remote_log_url, data)
	response = urllib2.urlopen(req)
	result = response.read()
	return result

###########################
# PERSONAL CONFIG FILE READ
###########################

parser = SafeConfigParser()
parser.read('watermeter_logger.ini')

# Read path to log file
LOG_FILENAME = parser.get('config', 'log_filename')

LOG_PERIOD = parser.getint('config', 'log_period')

#################
#  LOGGING SETUP
#################
logging.basicConfig()

LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
#handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

logger.info('Starting Watermeter logger')

GPIO.setwarnings(False)

pipes = [[0xf0, 0xf0, 0xf0, 0xf0, 0xe1], [0xf0, 0xf0, 0xf0, 0xf0, 0xd2]]

radio = NRF24()
radio.begin(0, 0,25,7) #set gpio 25 as CE pin
radio.setRetries(15,15)
radio.setPayloadSize(32)
radio.setChannel(0x4c)
radio.setDataRate(NRF24.BR_250KBPS)
radio.setPALevel(NRF24.PA_MAX)
radio.setAutoAck(1)
radio.openWritingPipe(pipes[0])
radio.openReadingPipe(1, pipes[1])

radio.startListening()

#radio.stopListening()
#radio.printDetails()
#radio.startListening()

old_counter_value = -1
total_in_period = 0
current_val = 0

def log_value():
	global total_in_period
	global current_val
	global old_counter_value
	
	logger.info('nb liters in last period: %d (current=%d, old=%d)' % (total_in_period, current_val, old_counter_value))

	res = remoteLog(total_in_period) 
	
	if not res=='\"insert OK\"':
		logger.info('remote log FAILED, status=' + res)

	total_in_period = 0

logger.info("log period: %d seconds", LOG_PERIOD)

scheduler = BackgroundScheduler()
scheduler.add_job(log_value, 'interval', seconds=LOG_PERIOD)
scheduler.start()

try:
	while True:
	    pipe = [0]
	    while not radio.available(pipe, True):
		time.sleep(0.333)
	    recv_buffer = []
	    radio.read(recv_buffer)
	    out = ''.join(chr(i) for i in recv_buffer)
	    #print out
	    params = out.split(":")
	    sensor = params[0]
	    message = params[1]
	    value = params[2].strip('\x00')
	    #logger.info('Received: %s' % params)
	    if (sensor == "water" and message == "top"):
		    current_val = int(value)
		    if (old_counter_value == -1):
		    	old_counter_value = current_val
		    else:
		    	delta = current_val - old_counter_value
		    	if (delta > 1):
		    		logger.info('MISSED tops (delta=%d)' % delta)
		    	total_in_period += delta
		    	old_counter_value = current_val

except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
	logger.info('EXITING watermeter logger')

