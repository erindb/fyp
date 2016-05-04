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


# from nltk.tokenize import WordPunctTokenizer
# from nltk import pos_tag
# from nltk.stem.wordnet import WordNetLemmatizer
# tokenizer = WordPunctTokenizer()
# def get_verbs(sentence):
#   # pick all the words in the sentence that are POS-tagged as verbs
#   # this is lame cause it picks up helping verbs...
#   # ...and isn't lemmatizing
#   sentence = tokenizer.tokenize(sentence)
#   return [w[0] for w in pos_tag(sentence) if w[1][0]=='V']

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
        return dep['dependentGloss']
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
          this_task[cond] = []
        this_cond = this_task[cond]
        this_cond.append(get_verbs(response))
        print tasks[index]

# for each cloze task,
  # for each condition,
    # % people who said original verb
    # % people who said most common verb

pickle.dump( tasks, open('tasks.p', 'wb') )