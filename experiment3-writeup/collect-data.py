#!/usr/bin/env python

import csv, codecs, cStringIO
import pickle
from collections import Counter

tasks = pickle.load( open('tasks.p', 'rb') )

for index in tasks:
  # for each cloze task,
  task = tasks[index]
  doc, chain, cloze = index
  orig_main_verb = task['orig_main_verb']
  for cond in ['caveman', 'original', 'event_only']:
    # for each condition,
    if cond in task:
      # % people who said original verb
      # % people who said most common verb
      response_verbs = task[cond]['response_verbs']
      all_response_verbs = [verb for verblist in response_verbs for verb in verblist]
      verb_counts = Counter(all_response_verbs)
      common = verb_counts.most_common(10)
      if common[0][0] == 'be' and len(common)>1:
        common = common[1:]
      most_common_verb = common[0][0]
      n_subj_most_common_verb = len([1 for verblist in response_verbs if most_common_verb in verblist])
      n_subj_match_orig = len([1 for verblist in response_verbs if orig_main_verb in verblist])
      n_subj = len(response_verbs)
      if n_subj > 2:
        percent_match_most_common = float(n_subj_most_common_verb - 1)/n_subj
        percent_match_orig = float(n_subj_match_orig)/n_subj
        print doc, chain, cloze, cond,
        print percent_match_orig,
        print percent_match_most_common,
        print n_subj_most_common_verb,
        print n_subj,
        print most_common_verb
      else:
        percent_match_most_common = None
        percent_match_orig = None
        print doc, chain, cloze, cond,
        print "NA",
        print "NA",
        print "NA",
        print "NA",
        print "NA"