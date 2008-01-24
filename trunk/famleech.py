#!/usr/bin/python

import httplib
import getopt
import sys
from collections import deque
import htmllib, formatter, urlparse


def append_gedcom(file, data, first):
	writing = False
	for line in data.split('\r\n'):
		elems = line.split()
		if len(elems) == 0:
			continue
		if int(elems[0]) == 0:
			if not first:
				writing = len(elems) == 3 and \
					(elems[2] == 'INDI' or elems[2] == 'FAM')
			else:
				writing = elems[1] != 'TRLR'
		if writing:
			file.write('%s\r\n' % line)


def leech(url):
	scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
	if scheme != 'http':
		print 'Malformed URL'
		sys.exit(-1)
	
	url = path + '?' + params + query
	slash = url.rindex('/')
	directory = url[:slash+1]
	file = url[slash+1:]
	conn = httplib.HTTPConnection(netloc)
	queue = deque([url])
	
	class Parser(htmllib.HTMLParser):
		def start_a(self, attrs):
			ref = dict(attrs)['href']
			if ref.startswith('pedigree_view.asp') or \
					ref.startswith('pedigree_chart_gedcom.asp'):
				queue.appendleft(directory + ref)
	
	parser = Parser(formatter.NullFormatter())
	
	file = open('result.ged', 'wb')
	
	count = 0
	while len(queue) > 0:
		url = queue.pop()
		print 'Requesting', url
		conn.request("GET", url)
		resp = conn.getresponse()
		data = resp.read()
		if 'pedigree_chart_gedcom.asp' in url:
			append_gedcom(file, data, count == 0)
			count = count + 1
			print 'Appended', count, 'gedcom files'
		parser.feed(data)
		parser.close()
	
	conn.close()
	
	file.write('0 TRLR\r\n')
	file.close()


if __name__ == '__main__':
	opts, args = getopt.getopt(sys.argv[1:], '')
	if len(args) != 1:
		print 'Usage: famleech.py <url>'
		sys.exit(-1)
	
	leech(args[0])
