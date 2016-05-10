#!/usr/bin/env python

import csv, codecs, cStringIO
import pickle

def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

import requests, json
def get_verbs(sentence):
  verbs = []
  r = requests.post('http://erindb.me/cgi-bin/nlp.py', data = {'text':sentence, 'annotators':'lemma,depparse'})
  sentence_data = json.loads(r.text)
  parsed_sentences = sentence_data['sentences']
  for parsed_sentence in parsed_sentences:
    for token in parsed_sentence['tokens']:
      # this is lame cause it picks up helping verbs...
      if token['pos'][0] == 'V':
        verbs.append(token['lemma'])
  print verbs
  return verbs
def get_main_verb(sentence):
  r = requests.post('http://erindb.me/cgi-bin/nlp.py', data = {'text':sentence, 'annotators':'lemma,depparse'})
  sentence_data = json.loads(r.text)
  parsed_sentences = sentence_data['sentences']
  for parsed_sentence in parsed_sentences:
    for dep in parsed_sentence['basic-dependencies']:
      if dep['dep'] == 'ROOT':
        depIndex = dep['dependent'] - 1
        # parsed_sentence['tokens'][depIndex]['lemma']
        return parsed_sentence['tokens'][depIndex]['lemma']
  return None

tasks = {}
main_verbs = {}

header = True
with codecs.open('experiment3.csv', 'rb', 'utf8') as csvfile:
    csvreader = unicode_csv_reader(csvfile)
    for row in csvreader:
      if header:
        header = False
      else:
        workerid, doc, chain, cloze, orig, gloss, response, cond, trial = row
        index = (doc, chain, cloze)
        if index not in tasks:
          tasks[index] = { "orig_main_verb": get_main_verb(orig) }
        this_task = tasks[index]
        if cond not in this_task:
          this_task[cond] = {"response_verbs": [], "responses": []}
        this_cond = this_task[cond]
        this_cond["response_verbs"].append(get_verbs(response))
        this_cond["responses"].append(response)
        print tasks[index]

pickle.dump( tasks, open('tasks.p', 'wb') )