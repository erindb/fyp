#!/usr/bin/env python

import csv
import urllib
import re
from bs4 import BeautifulSoup
import codecs

links_file = 'dinnersfromhell-links.csv'
links = []
with open(links_file, 'r') as csvfile:
	reader = csv.reader(csvfile)
	for row in reader:
		links.append(row[0])

i = 0
for link in links:
	if True: #i<20:
		link = links[i]
		f = urllib.urlopen(link)
		filestring = f.read()
		f.close()

		pattern = 'format_text entry-content\">\n((<p.*\n)*)<div class=\"pd-rating\"'

		m = re.search(pattern, filestring)
		if (m):
			source_code = m.group(1)

			soup = BeautifulSoup(source_code, "lxml")

			documentstring = soup.get_text()

			documentname = 'documents/dinnersfromhell-document-' + "%03d" % (i,) + '.txt'
			w = codecs.open(documentname, 'w', encoding='utf8')
			w.write(documentstring)
			w.close()
			i+=1
		else:
			w = open('documents/error.html', 'w')
			w.write(filestring)
			w.close()
			break

print 'finished'