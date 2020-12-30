#!/usr/bin/env python3
import json
import selenium
import os
import random
import datetime
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# for tagging debug images
DEBUG = False
DATA_DIR = 'data/scrape'

# create directory for images they don't exist
if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)

class CaptchaError(RuntimeError):
	def __init__(self, message='CaptchaError', errors=[]):
		# Call the base class constructor with the parameters it needs
		super(CaptchaError, self).__init__(message)

		# Now for your custom code...
		self.errors = errors

# simple class used to throttle submission rate
class SubmitThrottle():
	def __init__(self,period,**kwargs):
		self.prev_submit_time = None
		self.period = period
		self.jitter = kwargs.get('jitter',0)

	def now(self):
		return datetime.datetime.now().timestamp()

	def submitted(self):
		self.prev_submit_time = self.now()

	def block(self):
		if self.prev_submit_time:
			rand_jitter = random.randint(-self.jitter,self.jitter)
			wait_period = self.period + rand_jitter
			while wait_period > (self.now() - self.prev_submit_time):
				time.sleep(0.1)

class ZillowSession():
	HOME_URL = 'https://www.zillow.com/'
	SESSION_FILEPATH = os.path.join(DATA_DIR,'session.json')

	def __init__(self):
		self.driver = None
		self.throttle = SubmitThrottle(5,jitter=3)
		self.restore_session()

		# if we failed to restore session, make a new one
		if not self.driver:
			self.new_session()

		self.store_session()
		print('session_id = %s' % self.session_id())
		print('executor_url = %s' % self.executor_url())

	def executor_url(self):
		return self.driver.command_executor._url

	def session_id(self):
		return self.driver.session_id

	def get(self,url):
		self.throttle.block()
		self.throttle.submitted()
		self.driver.get(url)

	def new_session(self):
		print('creating new session...')
		# build list of Chrome options
		options = Options()
		# options.add_argument("--headless")

		# build path to Chrome webdriver
		BT_WEBDRIVERS_PATH = os.getenv('BT_WEBDRIVERS_PATH')
		if not BT_WEBDRIVERS_PATH:
			BT_WEBDRIVERS_PATH = './web_drivers'
			print("[WARNING] - 'BT_WEBDRIVERS_PATH' environment var is not set. Defaulting to '%s'." % BT_WEBDRIVERS_PATH)
		driver_path = os.path.join(
			BT_WEBDRIVERS_PATH,
			'linux64/chrome86/chromedriver')

		# open the driver
		self.driver = webdriver.Chrome(driver_path,options=options)

	def restore_session(self):
		if not os.path.exists(ZillowSession.SESSION_FILEPATH):
			print("Session file doesn't exist")
			return

		with open(ZillowSession.SESSION_FILEPATH,'r') as file:
			session_info = json.load(file)
			old_session_id = session_info['session_id']
			print('attempting to reclaim old session %s' % old_session_id)
			self.driver = webdriver.Remote(
				command_executor=session_info['executor_url'],
				desired_capabilities={})

			if self.driver.session_id != old_session_id:
				self.driver.close()
				self.driver.quit()

			# take the session that's already running
			self.driver.session_id = old_session_id

		# see if session exists, will raise if not
		try:
			self.driver.current_url
			print('restored session!')
		except:
			print('driver no longer exists...')
			self.driver = None

	def store_session(self):
		with open(ZillowSession.SESSION_FILEPATH,'w') as file:
			session_info = {
				'executor_url': self.executor_url(),
				'session_id': self.session_id()
			}
			json.dump(session_info,file)
