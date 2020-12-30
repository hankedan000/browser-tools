#!/usr/bin/env python3
import os
import traceback
import json
import argparse
import scrape.utils as zutils
from tqdm import tqdm
from scrape.listing import *
from scrape.results import *

LISTING_DATA_DIR = 'data/listings/'

def print_exception(e):
	traceback.print_tb(e.__traceback__)
	print(e)

if __name__ == '__main__':
	# create directory for listing data if doesn't exist
	if not os.path.exists(LISTING_DATA_DIR):
		os.makedirs(LISTING_DATA_DIR)

	parser = argparse.ArgumentParser(
		prog='scrape-listings',
		usage='%(prog)s [options]',
		description='Parses listing results from Zillow')

	parser.add_argument(
		'--from-url',
		type=str,
		help='parse listing reults from Zillow URL')

	parser.add_argument(
		'--from-html-file',
		type=argparse.FileType('r'),
		help='parse listing reults from html file')

	parser.add_argument(
		'--from-json-file',
		type=argparse.FileType('r'),
		help='parse listing reults from json file')

	parser.add_argument(
		'--force-reparse',
		action='store_true',default=False,
		help='forces a reparse of all stored HTML')

	args = parser.parse_args()

	zrs = ResultsScraper()
	zrs.session.store_session()
	zls = ListingScraper(session=zrs.session)
	results = []

	if args.from_html_file:
		results = zrs.get_results_from_file(args.from_html_file.name)
	elif args.from_json_file:
		results = json.load(args.from_json_file)
	elif args.from_url:
		results_url = args.from_url

		try:
			# parse results from first page
			zrs.session.get(results_url)
			zrs.write_html()
			print('parsing page %d...' % zrs.curr_page_num())
			results += zrs.get_results_from_page()

			while zrs.has_next_page():
				zrs.next_page()
				zrs.write_html()
				print('parsing page %d...' % zrs.curr_page_num())
				results += zrs.get_results_from_page()
		except KeyboardInterrupt:
			pass
		except Exception as e:
			print('Caught unknown exception!')
			print_exception(e)

	print('parsing %d result(s)...' % len(results))
	for url in tqdm(results):
		zpid = zutils.zpid_from_url(url)
		listing_dir = os.path.join(LISTING_DATA_DIR,zpid)
		listing_data_filepath = os.path.join(listing_dir,'listing_data.json')
		listing_html_filepath = os.path.join(listing_dir,'listing.html')

		if not os.path.exists(listing_dir):
			# make dir if it doesn't exist already
			os.makedirs(listing_dir)

		if os.path.exists(listing_data_filepath):
			if not args.force_reparse:
				# don't bother reparsing
				# TODO add force update flag
				continue

		details = None
		try:
			if os.path.exists(listing_html_filepath):
				details = zls.get_details_from_file(listing_html_filepath)
			else:
				zls.session.get(url)
				zls.write_html(listing_html_filepath)
				details = zls.get_details_from_page()
		except KeyboardInterrupt:
			break
		except CaptchaError as ce:
			# remove HTML for listings that raised the captcha error
			print('Caught a captcha error when processing zpid %s' % zpid)
			if os.path.exists(listing_html_filepath):
				os.remove(listing_html_filepath)
			exit()
		except Exception as e:
			print('Caught unknown exception while parsing zpid %s' % zpid)
			print_exception(e)
			details = None

		if details:
			with open(listing_data_filepath,'w') as f:
				json.dump(details,f,indent=4)
