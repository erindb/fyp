#!/usr/bin/python
# -*- coding: utf-8 -*-

def findDep(dependencies, depType=None, depTypes=None, governorIndex=None, depIndex=None):
  dependencies = findDeps(dependencies, depType=depType, depTypes=depTypes, governorIndex=governorIndex, depIndex=depIndex)
  if len(dependencies)==1:
    return dependencies[0]
  else:
    return None

def findDepIndex(dependencies, depType=None, depTypes=None, governorIndex=None, depIndex=None):
  dep = findDep(dependencies, depType=depType, depTypes=depTypes, governorIndex=governorIndex, depIndex=depIndex)
  if dep:
    return dep['dependent']
  else:
    return None

def findDeps(dependencies, depType=None, depTypes=None, governorIndex=None, depIndex=None):
  if depIndex:
    return filter(lambda dep: dep['dependent']==depIndex, dependencies)[0]

  if depTypes:
    all_matching_dependencies = []
    for depType in depTypes:
      all_matching_dependencies += findDeps(dependencies, depType=depType, governorIndex=governorIndex)
    return all_matching_dependencies

  if governorIndex:
    dependencies = filter(lambda dep: dep['governor']==governorIndex, dependencies)

  dependencies = filter(lambda dep: dep['dep']==depType, dependencies)
  return dependencies

def findToken(tokens, index):
  return filter(lambda x: x['index']==index, tokens)[0]

class LexicalItem:
  def __init__(self, text='', tokenData={}, dependencyData={}, corefs=[]):
    if text:
      self.text = text
    else:
      self.update(tokenData=tokenData,
        dependencyData=dependencyData,
        corefs=corefs)

  def update(self, tokenData={}, dependencyData={}, corefs=[]):
    if dependencyData:
      self.dep = dependencyData['dep']
      self.dependent = dependencyData['dependent']
      self.governorGloss = dependencyData['governorGloss']
      self.governor = dependencyData['governor']
      self.dependentGloss = dependencyData['dependentGloss']
      self.index = self.dependent
      self.text = self.dependentGloss
    if tokenData:
      self.word = tokenData['word']
      self.lemma = tokenData['lemma']
      self.ner = tokenData['ner']
      self.POS = tokenData['pos']
      self.text = self.lemma

class Sentence:
  def __init__(self, sentenceData):
    self.index = sentenceData['index']
    self.parse = sentenceData['parse']
    self.tokens = sentenceData['tokens']
    self.dependencies = sentenceData['basic-dependencies']

    # # lemma for active sentences,
    # # word for passive sentences
    self.head_verb_index = findDepIndex(self.dependencies, 'ROOT')
    self.head_verb = LexicalItem(
      dependencyData=findDep(self.dependencies, depIndex=self.head_verb_index),
      tokenData = findToken(self.tokens, index=self.head_verb_index)
    )

    ## if root is a VBN (past participle), check if it has an nsubjpass
    self.voice = 'active'
    if self.head_verb.POS == 'VBN':
      passive_subjects = findDeps(self.dependencies, governorIndex=self.head_verb_index, depType='nsubjpass')
      if len(passive_subjects) > 0:
        voice = 'passive'

    # # nsubj or nsubjpass
    # # also, what about conjunctions?
    # self.subject_index = 
    self.subject_index = findDepIndex(
      self.dependencies,
      governorIndex=self.head_verb_index,
      depTypes=['nsubj', 'nsubjpass'])
    self.subject = LexicalItem(
      dependencyData=findDep(self.dependencies, depIndex=self.subject_index),
      tokenData = findToken(self.tokens, index=self.subject_index)
    )

    self.direct_object = LexicalItem('bone')

    # keep the whole phrase for now
    self.prepositional_phrase = LexicalItem('in house')

    # true or false?
    self.negation = False

  def untokenize(self):
    words = map(lambda x: x['word'], self.tokens)
    result = ' '.join(words).replace(' ,',',').replace(' .','.').replace(' !','!')
    result = result.replace(' ?','?').replace(' :',': ').replace(' \'', '\'')
    return result

  def caveman(self):
    words = [
      self.subject.text,
      'not',
      self.head_verb.text,
      self.direct_object.text,
      self.prepositional_phrase.text
    ]
    if not self.negation:
      words.remove('not')
    return ' '.join(words).capitalize() + '.'

  ## how should I deal with coreferences across sentences?

one_sentence = Sentence(
  {
    "index": 0,
    "parse": "(ROOT\n  (S\n    (S\n      (NP (DT A) (JJ federal) (NN judge))\n      (VP (VBZ walks)\n        (PP (IN into)\n          (NP\n            (NP (DT a) (NN restaurant))\n            (PP (IN with)\n              (NP (DT a) (NN martini)))))))\n    (: ...)\n    (S\n      (S\n        (VP (VB Wait)))\n      (, ,)\n      (NP (DT that))\n      (VP (VBZ 's) (RB not)\n        (NP\n          (NP (DT a) (NN joke))\n          (, ,)\n          (SBAR\n            (WHNP (WDT that))\n            (S\n              (VP (VBD happened)\n                (NP-TMP (DT the) (JJ other) (NN night))))))))\n    (. .)))",
    "basic-dependencies": [
      {
        "dep": "ROOT",
        "governor": 0,
        "governorGloss": "ROOT",
        "dependent": 4,
        "dependentGloss": "walks"
      },
      {
        "dep": "det",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 1,
        "dependentGloss": "A"
      },
      {
        "dep": "amod",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 2,
        "dependentGloss": "federal"
      },
      {
        "dep": "nsubj",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 3,
        "dependentGloss": "judge"
      },
      {
        "dep": "case",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 5,
        "dependentGloss": "into"
      },
      {
        "dep": "det",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 6,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 7,
        "dependentGloss": "restaurant"
      },
      {
        "dep": "case",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 8,
        "dependentGloss": "with"
      },
      {
        "dep": "det",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 9,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 10,
        "dependentGloss": "martini"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 11,
        "dependentGloss": "..."
      },
      {
        "dep": "ccomp",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 12,
        "dependentGloss": "Wait"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 13,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 14,
        "dependentGloss": "that"
      },
      {
        "dep": "cop",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 15,
        "dependentGloss": "'s"
      },
      {
        "dep": "neg",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 16,
        "dependentGloss": "not"
      },
      {
        "dep": "det",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 17,
        "dependentGloss": "a"
      },
      {
        "dep": "parataxis",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 18,
        "dependentGloss": "joke"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 19,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 20,
        "dependentGloss": "that"
      },
      {
        "dep": "acl:relcl",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 21,
        "dependentGloss": "happened"
      },
      {
        "dep": "det",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 22,
        "dependentGloss": "the"
      },
      {
        "dep": "amod",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 23,
        "dependentGloss": "other"
      },
      {
        "dep": "nmod:tmod",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 24,
        "dependentGloss": "night"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 25,
        "dependentGloss": "."
      }
    ],
    "collapsed-dependencies": [
      {
        "dep": "ROOT",
        "governor": 0,
        "governorGloss": "ROOT",
        "dependent": 4,
        "dependentGloss": "walks"
      },
      {
        "dep": "det",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 1,
        "dependentGloss": "A"
      },
      {
        "dep": "amod",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 2,
        "dependentGloss": "federal"
      },
      {
        "dep": "nsubj",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 3,
        "dependentGloss": "judge"
      },
      {
        "dep": "case",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 5,
        "dependentGloss": "into"
      },
      {
        "dep": "det",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 6,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod:into",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 7,
        "dependentGloss": "restaurant"
      },
      {
        "dep": "case",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 8,
        "dependentGloss": "with"
      },
      {
        "dep": "det",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 9,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod:with",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 10,
        "dependentGloss": "martini"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 11,
        "dependentGloss": "..."
      },
      {
        "dep": "ccomp",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 12,
        "dependentGloss": "Wait"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 13,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 14,
        "dependentGloss": "that"
      },
      {
        "dep": "cop",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 15,
        "dependentGloss": "'s"
      },
      {
        "dep": "neg",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 16,
        "dependentGloss": "not"
      },
      {
        "dep": "det",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 17,
        "dependentGloss": "a"
      },
      {
        "dep": "parataxis",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 18,
        "dependentGloss": "joke"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 19,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 20,
        "dependentGloss": "that"
      },
      {
        "dep": "acl:relcl",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 21,
        "dependentGloss": "happened"
      },
      {
        "dep": "det",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 22,
        "dependentGloss": "the"
      },
      {
        "dep": "amod",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 23,
        "dependentGloss": "other"
      },
      {
        "dep": "nmod:tmod",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 24,
        "dependentGloss": "night"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 25,
        "dependentGloss": "."
      }
    ],
    "collapsed-ccprocessed-dependencies": [
      {
        "dep": "ROOT",
        "governor": 0,
        "governorGloss": "ROOT",
        "dependent": 4,
        "dependentGloss": "walks"
      },
      {
        "dep": "det",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 1,
        "dependentGloss": "A"
      },
      {
        "dep": "amod",
        "governor": 3,
        "governorGloss": "judge",
        "dependent": 2,
        "dependentGloss": "federal"
      },
      {
        "dep": "nsubj",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 3,
        "dependentGloss": "judge"
      },
      {
        "dep": "case",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 5,
        "dependentGloss": "into"
      },
      {
        "dep": "det",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 6,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod:into",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 7,
        "dependentGloss": "restaurant"
      },
      {
        "dep": "case",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 8,
        "dependentGloss": "with"
      },
      {
        "dep": "det",
        "governor": 10,
        "governorGloss": "martini",
        "dependent": 9,
        "dependentGloss": "a"
      },
      {
        "dep": "nmod:with",
        "governor": 7,
        "governorGloss": "restaurant",
        "dependent": 10,
        "dependentGloss": "martini"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 11,
        "dependentGloss": "..."
      },
      {
        "dep": "ccomp",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 12,
        "dependentGloss": "Wait"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 13,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 14,
        "dependentGloss": "that"
      },
      {
        "dep": "cop",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 15,
        "dependentGloss": "'s"
      },
      {
        "dep": "neg",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 16,
        "dependentGloss": "not"
      },
      {
        "dep": "det",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 17,
        "dependentGloss": "a"
      },
      {
        "dep": "parataxis",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 18,
        "dependentGloss": "joke"
      },
      {
        "dep": "punct",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 19,
        "dependentGloss": ","
      },
      {
        "dep": "nsubj",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 20,
        "dependentGloss": "that"
      },
      {
        "dep": "acl:relcl",
        "governor": 18,
        "governorGloss": "joke",
        "dependent": 21,
        "dependentGloss": "happened"
      },
      {
        "dep": "det",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 22,
        "dependentGloss": "the"
      },
      {
        "dep": "amod",
        "governor": 24,
        "governorGloss": "night",
        "dependent": 23,
        "dependentGloss": "other"
      },
      {
        "dep": "nmod:tmod",
        "governor": 21,
        "governorGloss": "happened",
        "dependent": 24,
        "dependentGloss": "night"
      },
      {
        "dep": "punct",
        "governor": 4,
        "governorGloss": "walks",
        "dependent": 25,
        "dependentGloss": "."
      }
    ],
    "tokens": [
      {
        "index": 1,
        "word": "A",
        "originalText": "A",
        "lemma": "a",
        "characterOffsetBegin": 0,
        "characterOffsetEnd": 1,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      },
      {
        "index": 2,
        "word": "federal",
        "originalText": "federal",
        "lemma": "federal",
        "characterOffsetBegin": 2,
        "characterOffsetEnd": 9,
        "pos": "JJ",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 3,
        "word": "judge",
        "originalText": "judge",
        "lemma": "judge",
        "characterOffsetBegin": 10,
        "characterOffsetEnd": 15,
        "pos": "NN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 4,
        "word": "walks",
        "originalText": "walks",
        "lemma": "walk",
        "characterOffsetBegin": 16,
        "characterOffsetEnd": 21,
        "pos": "VBZ",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 5,
        "word": "into",
        "originalText": "into",
        "lemma": "into",
        "characterOffsetBegin": 22,
        "characterOffsetEnd": 26,
        "pos": "IN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 6,
        "word": "a",
        "originalText": "a",
        "lemma": "a",
        "characterOffsetBegin": 27,
        "characterOffsetEnd": 28,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 7,
        "word": "restaurant",
        "originalText": "restaurant",
        "lemma": "restaurant",
        "characterOffsetBegin": 29,
        "characterOffsetEnd": 39,
        "pos": "NN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 8,
        "word": "with",
        "originalText": "with",
        "lemma": "with",
        "characterOffsetBegin": 40,
        "characterOffsetEnd": 44,
        "pos": "IN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 9,
        "word": "a",
        "originalText": "a",
        "lemma": "a",
        "characterOffsetBegin": 45,
        "characterOffsetEnd": 46,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 10,
        "word": "martini",
        "originalText": "martini",
        "lemma": "martini",
        "characterOffsetBegin": 47,
        "characterOffsetEnd": 54,
        "pos": "NN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": ""
      },
      {
        "index": 11,
        "word": "...",
        "originalText": "…",
        "lemma": "...",
        "characterOffsetBegin": 54,
        "characterOffsetEnd": 55,
        "pos": ":",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      },
      {
        "index": 12,
        "word": "Wait",
        "originalText": "Wait",
        "lemma": "wait",
        "characterOffsetBegin": 56,
        "characterOffsetEnd": 60,
        "pos": "VB",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": ""
      },
      {
        "index": 13,
        "word": ",",
        "originalText": ",",
        "lemma": ",",
        "characterOffsetBegin": 60,
        "characterOffsetEnd": 61,
        "pos": ",",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      },
      {
        "index": 14,
        "word": "that",
        "originalText": "that",
        "lemma": "that",
        "characterOffsetBegin": 62,
        "characterOffsetEnd": 66,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": ""
      },
      {
        "index": 15,
        "word": "'s",
        "originalText": "’s",
        "lemma": "be",
        "characterOffsetBegin": 66,
        "characterOffsetEnd": 68,
        "pos": "VBZ",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      },
      {
        "index": 16,
        "word": "not",
        "originalText": "not",
        "lemma": "not",
        "characterOffsetBegin": 69,
        "characterOffsetEnd": 72,
        "pos": "RB",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 17,
        "word": "a",
        "originalText": "a",
        "lemma": "a",
        "characterOffsetBegin": 73,
        "characterOffsetEnd": 74,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 18,
        "word": "joke",
        "originalText": "joke",
        "lemma": "joke",
        "characterOffsetBegin": 75,
        "characterOffsetEnd": 79,
        "pos": "NN",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": ""
      },
      {
        "index": 19,
        "word": ",",
        "originalText": ",",
        "lemma": ",",
        "characterOffsetBegin": 79,
        "characterOffsetEnd": 80,
        "pos": ",",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      },
      {
        "index": 20,
        "word": "that",
        "originalText": "that",
        "lemma": "that",
        "characterOffsetBegin": 81,
        "characterOffsetEnd": 85,
        "pos": "WDT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 21,
        "word": "happened",
        "originalText": "happened",
        "lemma": "happen",
        "characterOffsetBegin": 86,
        "characterOffsetEnd": 94,
        "pos": "VBD",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 22,
        "word": "the",
        "originalText": "the",
        "lemma": "the",
        "characterOffsetBegin": 95,
        "characterOffsetEnd": 98,
        "pos": "DT",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 23,
        "word": "other",
        "originalText": "other",
        "lemma": "other",
        "characterOffsetBegin": 99,
        "characterOffsetEnd": 104,
        "pos": "JJ",
        "ner": "O",
        "speaker": "PER0",
        "before": " ",
        "after": " "
      },
      {
        "index": 24,
        "word": "night",
        "originalText": "night",
        "lemma": "night",
        "characterOffsetBegin": 105,
        "characterOffsetEnd": 110,
        "pos": "NN",
        "ner": "TIME",
        "normalizedNER": "TNI",
        "speaker": "PER0",
        "before": " ",
        "after": "",
        "timex": {
          "tid": "t1",
          "type": "TIME",
          "value": "TNI"
        }
      },
      {
        "index": 25,
        "word": ".",
        "originalText": ".",
        "lemma": ".",
        "characterOffsetBegin": 110,
        "characterOffsetEnd": 111,
        "pos": ".",
        "ner": "O",
        "speaker": "PER0",
        "before": "",
        "after": " "
      }
    ]
  }
)

print one_sentence.untokenize()
print one_sentence.caveman()