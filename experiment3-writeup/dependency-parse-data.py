#!/usr/bin/env python

import csv
import os
import re
import json
from nltk.corpus import wordnet as wn

original_csv_file = 'experiment3-annotated.csv'

new_rows = []

response_sentences = []

csvfile = open(original_csv_file, 'rb')
csvreader = csv.DictReader(csvfile)
for row in csvreader:
	response_sentence = row['response'].strip()
	if re.match('[A-z]', response_sentence[-1]):
		response_sentence += '.'
	if re.match('.*[/,]$', response_sentence):
		response_sentence = response_sentence[:-1] + '.'
	response_sentences.append(response_sentence)
	new_rows.append(row)

# tmp_sentences_file = 'tmp-sentences-file.txt'
# with open(tmp_sentences_file, 'wb') as w:
# 	w.write('\n'.join(response_sentences))

# experiment_writeup_directory = os.getcwd()

# os.system("""
# wd=`pwd`
# cd ~/opt/corenlp
# java -cp "*" -Xmx8g edu.stanford.nlp.pipeline.StanfordCoreNLP """ +
# "-annotators tokenize,ssplit,pos,lemma,ner,parse,depparse " +
# "-file " + experiment_writeup_directory + "/" + tmp_sentences_file +
# " -outputFormat json " +
# "-outputDirectory " + experiment_writeup_directory +
# """ -replaceExtension
# cd $wd
# """)

def fix_index(i):
	return i-1

def get_root(sentence):
	root_index = fix_index(sentence['basic-dependencies'][0]['dependent'])
	word = sentence['tokens'][root_index]
	return (word['lemma'], word['pos'])

def get_synset(w, pos):
	pos = pos[0].lower()
	if pos=='j':
		pos = 'a'
	elif pos=='p':
		return w
	synsets = wn.synsets(w, pos)
	if len(synsets) == 0:
		return w
	return wn.synsets(w, pos)[0].name().split('.')[0]

dependency_parsed_file = 'tmp-sentences-file.json'
new_csv_file = 'experiment3-with-main-verbs.csv'

with open(dependency_parsed_file) as f:
	data = json.loads(f.read())
response_sentences = data['sentences']

new_rows = []

csvfile = open(original_csv_file, 'rb')
csvreader = csv.DictReader(csvfile)
for i, row in enumerate(csvreader):
	root_predicate, root_pos = get_root(response_sentences[i])
	synset = get_synset(root_predicate, root_pos)
	row['synset'] = synset
	row["root.predicate"] = root_predicate
	new_rows.append(row)

with open(new_csv_file, 'wb') as w:
	csvwriter = csv.DictWriter(w, fieldnames=new_rows[0].keys())
	csvwriter.writeheader()
	csvwriter.writerows(new_rows)