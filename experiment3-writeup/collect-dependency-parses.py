#!/usr/bin/env python

import csv
import os
import json

def main():

	original_csv_file = 'experiment3-annotated.csv'
	dependency_parsed_file = 'tmp-sentences-file.json'
	new_csv_file = 'experiment3-with-main-verbs.csv'

	with open(dependency_parsed_file) as f:
		data = json.loads(f.read())
	response_sentences = data['sentences']

	print len(response_sentences)

	new_rows = []

	csvfile = open(original_csv_file, 'rb')
	csvreader = csv.DictReader(csvfile)
	for i, row in enumerate(csvreader):
		root_predicate = get_root(response_sentences[i])
		row["root.predicate"] = root_predicate
		new_rows.append(row)

	with open(new_csv_file, 'wb') as w:
		csvwriter = csv.DictWriter(w, fieldnames=new_rows[0].keys())
		csvwriter.writeheader()
		csvwriter.writerows(new_rows)

def fix_index(i):
	return i-1

def get_root(sentence):
	root_index = fix_index(sentence['basic-dependencies'][0]['dependent'])
	return sentence['tokens'][root_index]['lemma']

main()