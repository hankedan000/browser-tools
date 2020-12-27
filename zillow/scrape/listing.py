#!/usr/bin/env python3
import json
import time
import selenium
import sys
import numpy
import datetime
import os
import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# for tagging debug images
DEBUG = False
DATA_DIR = 'data/scrape'

# create directory for images they don't exist
if not os.path.exists(DATA_DIR):
	os.makedirs(DATA_DIR)

# simple class used to throttle submission rate
class SubmitThrottle():
	def __init__(self,period):
		self.prev_submit_time = None
		self.period = period

	def now(self):
		return datetime.datetime.now().timestamp()

	def submitted(self):
		self.prev_submit_time = self.now()

	def block(self):
		if self.prev_submit_time:
			while self.period > (self.now() - self.prev_submit_time):
				time.sleep(0.1)

class ZillowSession():
	HOME_URL = 'https://www.zillow.com/'
	SESSION_FILEPATH = os.path.join(DATA_DIR,'session.json')

	def __init__(self):
		self.driver = None
		self.throttle = SubmitThrottle(1)
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
		self.driver.get(url)

	def new_session(self):
		print('creating new session...')
		# FIXME this assume you are running from root of repo
		# FIXME make this smarter
		self.driver = webdriver.Chrome('./web_drivers/linux64/chrome86/chromedriver')

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

class ListingScraper():
	def __init__(self):
		self.session = ZillowSession()

	def driver(self):
		return self.session.driver

	def get_statement_selector(self):
		return self.driver().find_element_by_id('eddstatementsnew.selecteddocument')

	def get_statement_options(self,selector):
		soup = BeautifulSoup(selector.get_attribute('innerHTML'),'html.parser')
		return soup.find_all('option')

	def start(self):
		pass
		# # waits for user to login
		# self.session.login()
		# # waits for user to select bank account
		# self.session.select_bank_account()

		# selector = self.get_statement_selector()
		# options = self.get_statement_options(selector)
		# options = options[1:]# first option is just "select-item"
		# print('Downloading %d statement(s)...' % len(options))
		# for option in tqdm.tqdm(options):
		# 	value = option.attrs['value']
		# 	option_elem = selector.find_element_by_xpath(
		# 		"option[text()='%s']" % option.text)
		# 	option_elem.click()

		# 	time.sleep(5)
