#!/usr/bin/env python3
import selenium
import sys
import scrape.utils as zutils
from scrape.session import *
from bs4 import BeautifulSoup

def get_classes(soup):
	attrs = soup.attrs
	if 'class' in attrs:
		return attrs['class']
	else:
		return []

class ResultsScraper():
	def __init__(self,**kwargs):
		if 'session' in kwargs:
			self.session = kwargs['session']
		else:
			self.session = ZillowSession()

	def driver(self):
		return self.session.driver

	def write_html(self,filepath='results.html'):
		with open(filepath,'w') as f:
			f.write(self.driver().page_source)

	def get_results_from_file(self,filepath='results.html'):
		with open(filepath,'r') as f:
			page_source = f.read()
			return self.parse_results_from_html(page_source)

	def get_results_from_url(self,results_url):
		self.session.get(results_url)
		return self.parse_results_from_html(self.driver().page_source)

	def get_results_from_page(self):
		return self.parse_results_from_html(self.driver().page_source)

	def _get_pagination_li(self):
		page = BeautifulSoup(self.driver().page_source,'html.parser')
		pagination = page.find('div',{'class','search-pagination'})
		if pagination:
			return pagination.findAll('li')
		return None

	def _next_page_a(self):
		pagination_li = self._get_pagination_li()
		if len(pagination_li) < 2:
			raise RuntimeError("pagination_li not long enough! length = %d" % len(pagination_li))

		return pagination_li[-1].find('a')

	def _prev_page_a(self):
		pagination_li = self._get_pagination_li()
		if len(pagination_li) < 2:
			raise RuntimeError("pagination_li not long enough! length = %d" % len(pagination_li))

		return pagination_li[0].find('a')

	def curr_page_num(self):
		pagination_li = self._get_pagination_li()
		for page_li in pagination_li:
			if 'aria-current' in page_li.attrs:
				return int(page_li.find('a').getText())
		return None

	def has_next_page(self,page_anchor=None):
		if not page_anchor:
			page_anchor = self._next_page_a()
		if page_anchor:
			return 'disabled' not in page_anchor.attrs
		return False

	def has_prev_page(self,page_anchor=None):
		if not page_anchor:
			page_anchor = self._prev_page_a()
		if page_anchor:
			return 'disabled' not in page_anchor.attrs
		return False

	def next_page(self):
		page_anchor = self._next_page_a()
		if self.has_next_page(page_anchor):
			self.session.get('https://zillow.com/' + page_anchor.attrs['href'])

	def prev_page(self):
		page_anchor = self._prev_page_a()
		if self.has_prev_page(page_anchor):
			self.session.get('https://zillow.com' + page_anchor.attrs['href'])

	def parse_results_from_html(self,results_html):
		DEBUG = False
		results = []
		page = BeautifulSoup(results_html,'html.parser')

		results_div = page.find('div',id='grid-search-results')
		results_ul = results_div.find('ul')
		for result_li in results_ul.findAll('li',recursive=False):
			list_card_link = result_li.find('a',{'class':'list-card-link'})
			if not list_card_link:
				continue
			listing_url = list_card_link.attrs['href']
			zpid = zutils.zpid_from_url(listing_url)
			results.append(listing_url)

		return results
