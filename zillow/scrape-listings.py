#!/usr/bin/env python3
import os
import json
from scrape.listing import *

if __name__ == '__main__':
	zls = ListingScraper()
	zls.session.store_session()
	details = None
	if os.path.exists('listing.html'):
		details = zls.get_details_from_file('listing.html')
	else:
		details = zls.get_details_from_url('https://www.zillow.com/homedetails/471-Preserve-Pointe-Blvd-33837-Davenport-FL-33837/2077035987_zpid/')
		zls.write_html()

	print(json.dumps(details,indent=4))