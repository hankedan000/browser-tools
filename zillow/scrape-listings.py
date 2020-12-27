#!/usr/bin/env python3
from scrape.listing import *

if __name__ == '__main__':
	zls = ListingScraper()
	zls.session.store_session()