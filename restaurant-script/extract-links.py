#!/usr/bin/env python

import re

f = open('dinners-from-hell-archive-index.html', 'r')
filestring = f.read()
f.close()

pattern = 'http://www\.dinnersfromhell\.com/..../../[A-z0-9-]*/'

matches = re.findall(pattern, filestring)

w = open('dinnersfromhell-links.csv', 'w')
w.write('\n'.join(matches))
w.close()