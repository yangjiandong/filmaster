#!/usr/bin/python

# Vote history converter, from the IMDb format to the Criticker format.
# Usage: ./imdb2criticker.py <imdb-vote-history-url>
#
# Tip: if you have the vote history HTML page stored locally, the file:// type URL will work too.
#
# (C)2008 Lukasz Bolikowski

import datetime
import re
import sys
import urllib

def parse(imdbVoteHistory):
	now = datetime.datetime.now().strftime("%b %d %Y, %H:%M")
	cvh = '<recentrankings>\n'
	id = None
	for line in imdbVoteHistory.split('\n'):
		line = line.strip()
		
		# Second line
		if id <> None:
			secondLine = re.match('<td[^>]*>(\d+)</td>', line)
			if secondLine <> None:
				vote = secondLine.group(1).strip()
				vote_criticker = int(vote) * 10
			cvh += '  <film>\n'
			cvh += '    <filmid>' + id + '</filmid>\n'
#			cvh += '    <filmname>' + title + " " + year + '</filmname>\n'
			cvh += '    <filmname>' + title + '</filmname>\n'
			cvh += '    <filmlink>http://www.imdb.com/title/tt' + id + '/</filmlink>\n'
			cvh += '    <img/>\n'
			cvh += '    <score>' + str(vote_criticker) + '</score>\n'
			cvh += '    <quote/>\n'
			cvh += '    <reviewdate>' + now + '</reviewdate>\n'
			cvh += '    <tier>' + vote + '</tier>\n'
			cvh += '  </film>\n'
		id = None

		# First line
		firstLine = re.match('<td [^>]* class="standard">.*<a href="/title/tt(\d+)/">([^>]+)</a>([^>]*)</td>', line)
		if firstLine <> None:
			id = firstLine.group(1).strip()
			title = firstLine.group(2).strip()
			year = firstLine.group(3).strip()
			continue
	cvh += '</recentrankings>\n'
	return cvh

if len(sys.argv) == 1:
	print "Usage %s <imdb-vote-history-url>" % sys.argv[0]
	sys.exit(1)
imdbUrl = sys.argv[1]
try:
	imdbVoteHistory = urllib.urlopen(imdbUrl).read()
	critickerVoteHistory = parse(imdbVoteHistory)
	print critickerVoteHistory,
except IOError:
	print "Could not get %s" % imdbUrl
	sys.exit(2)

