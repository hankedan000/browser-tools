#!/usr/bin/env python3

def zpid_from_url(url):
	zpid_idx = url.find('_zpid')
	if zpid_idx >= 0:
		slash_idx = url.rfind('/',0,zpid_idx)
		return url[slash_idx+1:zpid_idx]
	else:
		raise RuntimeError("Couldn't find zpid in url '%s'" % url)