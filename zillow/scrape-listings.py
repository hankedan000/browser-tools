#!/usr/bin/env python3
import os
import json
from scrape.listing import *
from scrape.results import *

if __name__ == '__main__':
	zrs = ResultsScraper()
	zrs.session.store_session()
	results = []

	if False and os.path.exists('results.html'):
		results = zrs.get_results_from_file('results.html')
	else:
		results_url = 'https://www.zillow.com/davenport-fl/'

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
		except:
			print('Caught unknown exception!')
			e = sys.exc_info()[0]
			print(str(e))

	print(json.dumps(results,indent=4))
