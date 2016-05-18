#!/usr/bin/env python

import csv, codecs, cStringIO
import pickle
from collections import Counter
from nltk.corpus import wordnet as wn

tasks = pickle.load( open('tasks.p', 'rb') )

def remotely_synonymous(a, b):
  ssa = set(wn.synsets(a, 'v'))
  ssb = set(wn.synsets(b, 'v'))
  return len(ssa.intersection(ssb))>0

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

      n_subj_loosely_match_orig = 0
      n_subj_loosely_match_mode = 0
      for verblist in response_verbs:
        subj_gave_loose_match = False
        subj_gave_loose_match_mode = False
        for verb in verblist:
          if remotely_synonymous(orig_main_verb, verb):
            subj_gave_loose_match = True
          if remotely_synonymous(most_common_verb, verb):
            subj_gave_loose_match_mode = True
        if subj_gave_loose_match:
          n_subj_loosely_match_orig += 1

      n_subj = len(response_verbs)
      percent_match_most_common = float(n_subj_most_common_verb - 1)/n_subj
      percent_match_orig = float(n_subj_match_orig)/n_subj
      print doc, chain, cloze, cond,
      print percent_match_orig,
      print percent_match_most_common,
      print n_subj_most_common_verb - 1,
      print n_subj,
      print most_common_verb,
      print n_subj_loosely_match_orig,
      print orig_main_verb,
      print n_subj_loosely_match_mode