#!/usr/bin/python
#License LGPL
#Authors, Neil Toronto and James L. Carroll


import httplib
import socket
import getopt
import sys
from collections import deque
import htmllib, formatter, urlparse
from random import random
from time import sleep

version="0.3.2"

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
    file = open('result.ged','wb')
    leechedURLSet=set([])
    count = 0
    while len(queue) > 0:
	url = queue.pop()
	if url in leechedURLSet:
	    print "Repeat URL:",url
	else:
	    leechedURLSet.add(url)
	    while True:
		delay = 5 * random()
		sleep(delay)
		try:
		    print 'Requesting', url
		    conn.request("GET", url)
		    resp = conn.getresponse()
		    respSuccess=True
		    break
		except (httplib.HTTPException, socket.error), e:
		    # Recreating the HTTPConnection, just in case
		    conn = httplib.HTTPConnection(netloc)
		    respSuccess=False
		    print "Got an exception while downloading \"%s\"" % url
		    print e, repr(e)
		    print "Waiting to retry (hit CTRL-c to skip)"
		    try:
			sleep(55)
			print "Retrying"
			sleep(5)
		    except KeyboardInterrupt:
			print "Giving up"
			break
	    if respSuccess==True:
		data = resp.read()
		if 'pedigree_chart_gedcom.asp' in url:
		    append_gedcom(file, data, count ==0)
		    #f = open('%04d.ged' % count, 'wb')
		    #f.write(data)
		    #f.close()
		    count = count + 1
		    print 'Appended',count,'gedcom files,',len(queue),'pages still in the queue.'
		parser.feed(data)
		parser.close()

    conn.close()

    #printing the footer on the gedcom file
    file.write('0 TRLR\r\n')
    file.close


if __name__ == '__main__':
    print "famleech version",version
    opts, args = getopt.getopt(sys.argv[1:], '')
    if len(args) != 1:
	print 'Usage: famleech.py <url>'
	sys.exit(-1)
    leech(args[0])
