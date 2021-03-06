#!/usr/bin/env python3
import selenium
import sys
import scrape.utils as zutils
from scrape.session import *
from bs4 import BeautifulSoup

def parse_comma_num(comma_num_text,**kwargs):
	default = kwargs.get('default',None)
	try:
		return float(comma_num_text.replace(',',''))
	except:
		return default

def parse_price(price_text):
	price_text = price_text.replace('$','')
	return parse_comma_num(price_text,default=0.0)

def get_meta_content(head_soup,prop_name):
	return head_soup.find('meta',property=prop_name).attrs['content']

class ListingScraper():
	def __init__(self,**kwargs):
		if 'session' in kwargs:
			self.session = kwargs['session']
		else:
			self.session = ZillowSession()

	def driver(self):
		return self.session.driver

	def write_html(self,filepath='listing.html'):
		with open(filepath,'w') as f:
			f.write(self.driver().page_source)

	def get_details_from_file(self,filepath='listing.html',**kwargs):
		with open(filepath,'r') as f:
			page_source = f.read()
			return self.parse_details_from_html(page_source,**kwargs)

	def get_details_from_url(self,listing_url,**kwargs):
		self.session.get(listing_url)
		return self.parse_details_from_html(self.driver().page_source,**kwargs)

	def get_details_from_page(self,**kwargs):
		return self.parse_details_from_html(self.driver().page_source,**kwargs)

	def parse_details_from_html(self,listing_html,**kwargs):
		DEBUG = kwargs.get('debug',False)
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
			'built_year': -1,
			'heating': 'No Data',
			'cooling': 'No Data',
			'hoa_monthly': -1,
			'lot_size': '',
			'parking': [],
			'image_urls': [],
			'image_files': [],
		}
		page = BeautifulSoup(listing_html,'html.parser')

		captcha = page.find('div',{'class':'captcha-container'})
		if captcha:
			raise CaptchaError()

		summary = page.find('div',{'class':'ds-summary-row'})
		summary_children = []
		if summary:
			summary.findChildren()
		if DEBUG:
			print('-------------- SUMMARY --------------')
			idx = 0
			for child in summary_children:
				print('%d: %s' % (idx,child))
				idx += 1
		if len(summary_children) >= 16:
			sqft = summary_children[15].getText().replace('sqft','')
			details['sqft'] = parse_comma_num(sqft,default=0.0)

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
		details['zpid'] = zutils.zpid_from_url(url)

		# parse MLS # from title
		title = get_meta_content(head,'og:title')
		title_parts = title.split('|')
		for title_part in title_parts:
			if 'MLS #' in title_part:
				mls = title_part.replace('MLS #','')
				details['mls'] = mls.strip()
				break

		# parse list of home facts
		facts = page.find('ul',{'class':'ds-home-fact-list'})
		facts_children = []
		if facts:
			facts_children = facts.findChildren()
		for fact in facts_children:
			fact_children = fact.findChildren()
			if len(fact_children) == 0:
				continue

			icon = fact_children[0]
			icon_classes = icon.attrs['class']
			try:
				if 'zsg-icon-heat' in icon_classes:
					details['heating'] = fact_children[2].getText()
				elif 'zsg-icon-snowflake' in icon_classes:
					details['cooling'] = fact_children[2].getText()
				elif 'zsg-icon-calendar' in icon_classes:
					details['built_year'] = parse_comma_num(fact_children[2].getText(),default=0)
				elif 'zsg-icon-lot' in icon_classes:
					details['lot_size'] = fact_children[2].getText()
				elif 'zsg-icon-parking' in icon_classes:
					details['parking'] = fact_children[2].getText().split(',')
				elif 'zsg-icon-hoa' in icon_classes:
					hoa = fact_children[2].getText().replace('/mo','')
					details['hoa_monthly'] = parse_price(hoa)
			except ValueError as ve:
				if 'No Data' in str(ve):
					# zillow will place 'No Data' in some of the
					# fact fields. this is an expected exception
					pass
				else:
					raise ve

		# parse list of images
		media = page.find('ul',{'class':'media-stream'})
		media_lis = []
		if media:
			media_lis = media.findAll('li')
		for media_li in media_lis:
			img = media_li.find('img')
			if img:
				img_url = img.attrs['src']
				url_parts = img_url.split('/')
				details['image_urls'].append(img_url)
				details['image_files'].append(url_parts[-1])

		return details
