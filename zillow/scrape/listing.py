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

def parse_comma_num(comma_num_text):
	num_text = comma_num_text.replace(',','')
	return float(num_text)

def parse_price(price_text):
	price_text = price_text.replace('$','')
	return parse_comma_num(price_text)

def get_meta_content(head_soup,prop_name):
	return head_soup.find('meta',property=prop_name).attrs['content']

class ListingScraper():
	def __init__(self):
		self.session = ZillowSession()

	def driver(self):
		return self.session.driver

	def write_html(self,filepath='listing.html'):
		with open(filepath,'w') as f:
			f.write(self.driver().page_source)

	def get_details_from_file(self,filepath='listing.html'):
		with open(filepath,'r') as f:
			page_source = f.read()
			return self.parse_details_from_html(page_source)

	def get_details_from_url(self,listing_url):
		self.session.get(listing_url)
		return self.parse_details_from_html(self.driver().page_source)

	def parse_details_from_html(self,listing_html):
		DEBUG = False
		details = {
			'zpid': '',
			'mls': '',
			'url': '',
			'price': -1,
			'currency': 'USD',
			'sqft': -1,
			'address': '',
			'beds': -1,
			'baths': -1,
			'description': '',
			'type': '',
		}
		page = BeautifulSoup(listing_html,'html.parser')
		summary = page.find('div',{'class':'ds-summary-row'})
		summary_children = summary.findChildren()
		if DEBUG:
			print('-------------- SUMMARY --------------')
			idx = 0
			for child in summary_children:
				print('%d: %s' % (idx,child))
				idx += 1
		details['sqft'] = parse_comma_num(summary_children[15].getText())

		head = page.find('head')
		details['price'] = float(get_meta_content(head,'product:price:amount'))
		details['currency'] = get_meta_content(head,'product:price:currency')
		details['address'] = get_meta_content(head,'og:zillow_fb:address')
		details['beds'] = int(get_meta_content(head,'zillow_fb:beds'))
		details['baths'] = int(get_meta_content(head,'zillow_fb:baths'))
		details['description'] = get_meta_content(head,'zillow_fb:description')
		details['type'] = get_meta_content(head,'og:type')

		# parse zpid from listing url
		url = get_meta_content(head,'og:url')
		details['url'] = url
		zpid_idx = url.find('_zpid')
		if zpid_idx >= 0:
			slash_idx = url.rfind('/',0,zpid_idx)
			details['zpid'] = url[slash_idx+1:zpid_idx]
		else:
			raise RuntimeError("Couldn't find zpid in url '%s'" % url)

		# parse MLS # from title
		title = get_meta_content(head,'og:title')
		title_parts = title.split('|')
		for title_part in title_parts:
			if 'MLS #' in title_part:
				mls = title_part.replace('MLS #','')
				details['mls'] = mls.strip()
				break

		return details
