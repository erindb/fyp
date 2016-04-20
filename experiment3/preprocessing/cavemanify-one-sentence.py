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

def findDepIndices(dependencies, depType=None, depTypes=None, governorIndex=None, depIndex=None):
  deps = findDeps(dependencies, depType=depType, depTypes=depTypes, governorIndex=governorIndex, depIndex=depIndex)
  if deps:
    return map(lambda dep: dep['dependent'], deps)
  else:
    return None

def findDeps(dependencies, depType=None, depTypes=None, governorIndex=None, depIndex=None):
  if depIndex:
    return filter(lambda dep: dep['dependent']==depIndex, dependencies)

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

    self.references = []
    if corefs:
      for coref_id in corefs:
        references = corefs[coref_id]
        for reference in references:
          startIndex = reference['startIndex']
          endIndex = reference['endIndex']
          if (self.index >= startIndex and self.index <= endIndex):
            self.references.append(reference)


class Sentence:
  def __init__(self, sentenceData, corefsData):
    self.index = sentenceData['index']
    self.parse = sentenceData['parse']
    self.tokens = sentenceData['tokens']
    self.dependencies = sentenceData['collapsed-dependencies']

    ## for each referent, pick the shortest representative mention
    self.coreferences = {}
    for coref_id in corefsData:
        references = corefsData[coref_id]
        # print references
        localReferences = filter(lambda ref: (int(ref['sentNum'])-1)==self.index, references)
        if len(localReferences)>0:
          representativeMention = 'placeholder'
          representativeMentionStrings = map(lambda ref: ref['text'],
            filter(lambda ref: ref['isRepresentativeMention'],
              references))
          minlen = min(map(lambda s: len(s), representativeMentionStrings))
          representativeMention = filter(lambda s: len(s)==minlen, representativeMentionStrings)[0]
          for reference in references:
            reference['representativeMention'] = representativeMention
          self.coreferences[coref_id] = references

    # # lemma for active sentences,
    # # word for passive sentences
    head_verb_index = findDepIndex(self.dependencies, 'ROOT')
    self.head_verb = LexicalItem(
      dependencyData=findDep(self.dependencies, depIndex=head_verb_index),
      tokenData = findToken(self.tokens, index=head_verb_index),
      corefs = self.coreferences
    )

    ## if root is a VBN (past participle), check if it has an nsubjpass
    self.voice = 'active'
    if self.head_verb.POS == 'VBN':
      passive_subjects = findDeps(self.dependencies, governorIndex=head_verb_index, depType='nsubjpass')
      if len(passive_subjects) > 0:
        voice = 'passive'

    # # nsubj or nsubjpass
    # # also, what about conjunctions?
    # subject_index = 
    subject_index = findDepIndex(
      self.dependencies,
      governorIndex=head_verb_index,
      depTypes=['nsubj', 'nsubjpass'])
    self.subject = LexicalItem(
      dependencyData=findDep(self.dependencies, depIndex=subject_index),
      tokenData = findToken(self.tokens, index=subject_index),
      corefs = self.coreferences
    )

    direct_object_index = findDepIndex(
      self.dependencies,
      governorIndex=head_verb_index,
      depType=['dobj'])
    if direct_object_index:
      self.direct_object = LexicalItem(
        dependencyData=findDep(self.dependencies, depIndex=direct_object_index),
        tokenData = findToken(self.tokens, index=direct_object_index),
        corefs = self.coreferences
      )
    else:
      self.direct_object = None

    # keep the whole phrase for now
    prepositional_phrase_indices = findDepIndices(
      self.dependencies,
      governorIndex=head_verb_index,
      depTypes=[
        'nmod:into',
        'nmod:with',
        'nmod:for',
        'nmod:to',
        'nmod:after',
        'nmod:before',
        'nmod:towards',
        'nmod:on',
        'nmod:in'])
    self.prepositional_phrases = []
    for prepositional_phrase_index in prepositional_phrase_indices:
      self.prepositional_phrases.append(LexicalItem(
        dependencyData=findDep(self.dependencies, depIndex=prepositional_phrase_index),
        tokenData = findToken(self.tokens, index=prepositional_phrase_index),
        corefs = self.coreferences
      ))

    # true or false?
    self.negation = False

  def untokenize(self):
    words = map(lambda x: x['word'], self.tokens)
    result = ' '.join(words).replace(' ,',',').replace(' .','.').replace(' !','!')
    result = result.replace(' ?','?').replace(' :',': ').replace(' \'', '\'')
    return result

  def caveman(self):
    words = []
    words.append(self.subject.text)

    if self.negation:
      words.append('not')

    words.append(self.head_verb.text)

    if self.direct_object:
      words.append(self.direct_object.text)

    for pp in self.prepositional_phrases:
      words.append(pp.dep[5:])
      words.append(pp.text)

    return ' '.join(words).capitalize() + '.'

  def event_only(self):
    words = []

    ## actually only do this when subject is the coreferring entity
    words.append(self.subject.text)

    words.append(self.head_verb.text)

    ## if the coreferring entity is not the subject, then mention it
    return ' '.join(words).capitalize() + '.'

  ## how should I deal with coreferences across sentences?
  ## references are now passed down to the lexical items themselves...

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
  },
  {
    "1": [
      {
        "id": 1,
        "text": "A federal judge",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 4,
        "sentNum": 1,
        "position": [
          1,
          1
        ],
        "isRepresentativeMention": True
      }
    ],
    "65": [
      {
        "id": 65,
        "text": "Most restaurants",
        "type": "NOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 1,
        "endIndex": 3,
        "sentNum": 11,
        "position": [
          11,
          1
        ],
        "isRepresentativeMention": True
      }
    ],
    "2": [
      {
        "id": 2,
        "text": "a restaurant with a martini",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 6,
        "endIndex": 11,
        "sentNum": 1,
        "position": [
          1,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 8,
        "text": "it ",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 4,
        "endIndex": 5,
        "sentNum": 2,
        "position": [
          2,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 12,
        "text": "it",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 12,
        "endIndex": 13,
        "sentNum": 2,
        "position": [
          2,
          5
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 50,
        "text": "the restaurant",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 6,
        "endIndex": 8,
        "sentNum": 7,
        "position": [
          7,
          3
        ],
        "isRepresentativeMention": False
      }
    ],
    "3": [
      {
        "id": 3,
        "text": "a martini",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 9,
        "endIndex": 11,
        "sentNum": 1,
        "position": [
          1,
          3
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 4,
        "text": "that",
        "type": "PRONOMINAL",
        "number": "UNKNOWN",
        "gender": "NEUTRAL",
        "animacy": "UNKNOWN",
        "startIndex": 14,
        "endIndex": 15,
        "sentNum": 1,
        "position": [
          1,
          4
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 5,
        "text": "a joke, that happened the other night",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 17,
        "endIndex": 25,
        "sentNum": 1,
        "position": [
          1,
          5
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 6,
        "text": "a joke",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 17,
        "endIndex": 19,
        "sentNum": 1,
        "position": [
          1,
          6
        ],
        "isRepresentativeMention": False
      }
    ],
    "67": [
      {
        "id": 67,
        "text": "this",
        "type": "NOMINAL",
        "number": "UNKNOWN",
        "gender": "NEUTRAL",
        "animacy": "UNKNOWN",
        "startIndex": 3,
        "endIndex": 4,
        "sentNum": 12,
        "position": [
          12,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 71,
        "text": "it",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 9,
        "endIndex": 10,
        "sentNum": 13,
        "position": [
          13,
          3
        ],
        "isRepresentativeMention": False
      }
    ],
    "68": [
      {
        "id": 68,
        "text": "a more gracious fashion",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 9,
        "endIndex": 13,
        "sentNum": 12,
        "position": [
          12,
          3
        ],
        "isRepresentativeMention": True
      }
    ],
    "7": [
      {
        "id": 7,
        "text": "the other night",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 22,
        "endIndex": 25,
        "sentNum": 1,
        "position": [
          1,
          7
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 34,
        "text": "night",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 16,
        "endIndex": 17,
        "sentNum": 4,
        "position": [
          4,
          7
        ],
        "isRepresentativeMention": False
      }
    ],
    "72": [
      {
        "id": 72,
        "text": "our evening",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 12,
        "endIndex": 14,
        "sentNum": 13,
        "position": [
          13,
          4
        ],
        "isRepresentativeMention": True
      }
    ],
    "9": [
      {
        "id": 9,
        "text": " a violation of my liquor license",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 5,
        "endIndex": 11,
        "sentNum": 2,
        "position": [
          2,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 17,
        "text": "it",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 23,
        "endIndex": 24,
        "sentNum": 3,
        "position": [
          3,
          5
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 18,
        "text": "a violation of our liquor license",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 25,
        "endIndex": 31,
        "sentNum": 3,
        "position": [
          3,
          6
        ],
        "isRepresentativeMention": False
      }
    ],
    "10": [
      {
        "id": 10,
        "text": "my liquor license",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 8,
        "endIndex": 11,
        "sentNum": 2,
        "position": [
          2,
          3
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 19,
        "text": "our liquor license",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 28,
        "endIndex": 31,
        "sentNum": 3,
        "position": [
          3,
          7
        ],
        "isRepresentativeMention": False
      }
    ],
    "74": [
      {
        "id": 74,
        "text": "Thought you",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 1,
        "endIndex": 3,
        "sentNum": 14,
        "position": [
          14,
          1
        ],
        "isRepresentativeMention": True
      }
    ],
    "11": [
      {
        "id": 11,
        "text": "my",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 8,
        "endIndex": 9,
        "sentNum": 2,
        "position": [
          2,
          4
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 13,
        "text": "I",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 3,
        "position": [
          3,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 21,
        "text": "I",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 32,
        "endIndex": 33,
        "sentNum": 3,
        "position": [
          3,
          9
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 37,
        "text": "I",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 2,
        "endIndex": 3,
        "sentNum": 5,
        "position": [
          5,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 66,
        "text": "I",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 12,
        "position": [
          12,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 69,
        "text": "I",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 2,
        "endIndex": 3,
        "sentNum": 13,
        "position": [
          13,
          1
        ],
        "isRepresentativeMention": False
      }
    ],
    "14": [
      {
        "id": 14,
        "text": "a manager",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 3,
        "endIndex": 5,
        "sentNum": 3,
        "position": [
          3,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 24,
        "text": "he",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 42,
        "endIndex": 43,
        "sentNum": 3,
        "position": [
          3,
          12
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 26,
        "text": "his",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 46,
        "endIndex": 47,
        "sentNum": 3,
        "position": [
          3,
          14
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 39,
        "text": "the manager",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 10,
        "endIndex": 12,
        "sentNum": 5,
        "position": [
          5,
          3
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 53,
        "text": "the manager",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 10,
        "endIndex": 12,
        "sentNum": 8,
        "position": [
          8,
          3
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 54,
        "text": "He",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 9,
        "position": [
          9,
          1
        ],
        "isRepresentativeMention": False
      }
    ],
    "15": [
      {
        "id": 15,
        "text": "the drink",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 12,
        "endIndex": 14,
        "sentNum": 3,
        "position": [
          3,
          3
        ],
        "isRepresentativeMention": True
      }
    ],
    "79": [
      {
        "id": 79,
        "text": "the floor",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 14,
        "endIndex": 16,
        "sentNum": 15,
        "position": [
          15,
          4
        ],
        "isRepresentativeMention": True
      }
    ],
    "16": [
      {
        "id": 16,
        "text": "a scene",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 16,
        "endIndex": 18,
        "sentNum": 3,
        "position": [
          3,
          4
        ],
        "isRepresentativeMention": True
      }
    ],
    "80": [
      {
        "id": 80,
        "text": "better",
        "type": "NOMINAL",
        "number": "UNKNOWN",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 5,
        "endIndex": 6,
        "sentNum": 16,
        "position": [
          16,
          1
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 82,
        "text": "it",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 10,
        "endIndex": 11,
        "sentNum": 16,
        "position": [
          16,
          3
        ],
        "isRepresentativeMention": False
      }
    ],
    "81": [
      {
        "id": 81,
        "text": "you",
        "type": "PRONOMINAL",
        "number": "UNKNOWN",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 7,
        "endIndex": 8,
        "sentNum": 16,
        "position": [
          16,
          2
        ],
        "isRepresentativeMention": True
      }
    ],
    "20": [
      {
        "id": 20,
        "text": "our",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 28,
        "endIndex": 29,
        "sentNum": 3,
        "position": [
          3,
          8
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 30,
        "text": "we",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 5,
        "endIndex": 6,
        "sentNum": 4,
        "position": [
          4,
          3
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 31,
        "text": "We",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 9,
        "endIndex": 10,
        "sentNum": 4,
        "position": [
          4,
          4
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 36,
        "text": "our",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 18,
        "endIndex": 19,
        "sentNum": 4,
        "position": [
          4,
          9
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 40,
        "text": "us",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 16,
        "endIndex": 17,
        "sentNum": 5,
        "position": [
          5,
          4
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 41,
        "text": "We",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 6,
        "position": [
          6,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 45,
        "text": "our",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 6,
        "endIndex": 7,
        "sentNum": 6,
        "position": [
          6,
          5
        ],
        "isRepresentativeMention": False
      }
    ],
    "84": [
      {
        "id": 84,
        "text": "his sense of entitlement",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 16,
        "endIndex": 20,
        "sentNum": 16,
        "position": [
          16,
          5
        ],
        "isRepresentativeMention": True
      }
    ],
    "22": [
      {
        "id": 22,
        "text": "this guest to keep the martini he had dumped into his wine glass",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 36,
        "endIndex": 49,
        "sentNum": 3,
        "position": [
          3,
          10
        ],
        "isRepresentativeMention": True
      }
    ],
    "23": [
      {
        "id": 23,
        "text": "the martini he had dumped into his wine glass",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 40,
        "endIndex": 49,
        "sentNum": 3,
        "position": [
          3,
          11
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 46,
        "text": "his martini",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 12,
        "endIndex": 14,
        "sentNum": 6,
        "position": [
          6,
          6
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 77,
        "text": "his martini",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 11,
        "endIndex": 13,
        "sentNum": 15,
        "position": [
          15,
          2
        ],
        "isRepresentativeMention": False
      }
    ],
    "25": [
      {
        "id": 25,
        "text": "his wine glass",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 46,
        "endIndex": 49,
        "sentNum": 3,
        "position": [
          3,
          13
        ],
        "isRepresentativeMention": True
      }
    ],
    "27": [
      {
        "id": 27,
        "text": "36th",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "UNKNOWN",
        "startIndex": 19,
        "endIndex": 20,
        "sentNum": 4,
        "position": [
          4,
          10
        ],
        "isRepresentativeMention": True
      }
    ],
    "28": [
      {
        "id": 28,
        "text": "This",
        "type": "NOMINAL",
        "number": "UNKNOWN",
        "gender": "NEUTRAL",
        "animacy": "UNKNOWN",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 4,
        "position": [
          4,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 29,
        "text": "the email we got:\n“We had a very nice dinner Wednesday night celebrating our 36th anniversary",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 3,
        "endIndex": 21,
        "sentNum": 4,
        "position": [
          4,
          2
        ],
        "isRepresentativeMention": True
      }
    ],
    "32": [
      {
        "id": 32,
        "text": "a very nice dinner",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 11,
        "endIndex": 15,
        "sentNum": 4,
        "position": [
          4,
          5
        ],
        "isRepresentativeMention": True
      }
    ],
    "33": [
      {
        "id": 33,
        "text": "Wednesday",
        "type": "PROPER",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 15,
        "endIndex": 16,
        "sentNum": 4,
        "position": [
          4,
          6
        ],
        "isRepresentativeMention": True
      }
    ],
    "35": [
      {
        "id": 35,
        "text": "our 36th anniversary",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 18,
        "endIndex": 21,
        "sentNum": 4,
        "position": [
          4,
          8
        ],
        "isRepresentativeMention": True
      }
    ],
    "38": [
      {
        "id": 38,
        "text": "you",
        "type": "PRONOMINAL",
        "number": "UNKNOWN",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 4,
        "endIndex": 5,
        "sentNum": 5,
        "position": [
          5,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 75,
        "text": "you",
        "type": "PRONOMINAL",
        "number": "UNKNOWN",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 2,
        "endIndex": 3,
        "sentNum": 14,
        "position": [
          14,
          2
        ],
        "isRepresentativeMention": False
      }
    ],
    "42": [
      {
        "id": 42,
        "text": "the limo and our best man",
        "type": "LIST",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 3,
        "endIndex": 9,
        "sentNum": 6,
        "position": [
          6,
          2
        ],
        "isRepresentativeMention": True
      }
    ],
    "43": [
      {
        "id": 43,
        "text": "the limo",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 3,
        "endIndex": 5,
        "sentNum": 6,
        "position": [
          6,
          3
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 49,
        "text": "it",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 4,
        "endIndex": 5,
        "sentNum": 7,
        "position": [
          7,
          2
        ],
        "isRepresentativeMention": False
      }
    ],
    "44": [
      {
        "id": 44,
        "text": "our best man",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 6,
        "endIndex": 9,
        "sentNum": 6,
        "position": [
          6,
          4
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 47,
        "text": "his",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 12,
        "endIndex": 13,
        "sentNum": 6,
        "position": [
          6,
          7
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 48,
        "text": "he",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 2,
        "endIndex": 3,
        "sentNum": 7,
        "position": [
          7,
          1
        ],
        "isRepresentativeMention": False
      }
    ],
    "51": [
      {
        "id": 51,
        "text": "The hostess",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "FEMALE",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 3,
        "sentNum": 8,
        "position": [
          8,
          1
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 52,
        "text": "she",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "FEMALE",
        "animacy": "ANIMATE",
        "startIndex": 4,
        "endIndex": 5,
        "sentNum": 8,
        "position": [
          8,
          2
        ],
        "isRepresentativeMention": False
      }
    ],
    "55": [
      {
        "id": 55,
        "text": "the table",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 5,
        "endIndex": 7,
        "sentNum": 9,
        "position": [
          9,
          2
        ],
        "isRepresentativeMention": True
      }
    ],
    "56": [
      {
        "id": 56,
        "text": "the drink with nary a word",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "NEUTRAL",
        "animacy": "INANIMATE",
        "startIndex": 10,
        "endIndex": 16,
        "sentNum": 9,
        "position": [
          9,
          3
        ],
        "isRepresentativeMention": True
      }
    ],
    "57": [
      {
        "id": 57,
        "text": "nary a word",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "INANIMATE",
        "startIndex": 13,
        "endIndex": 16,
        "sentNum": 9,
        "position": [
          9,
          4
        ],
        "isRepresentativeMention": True
      }
    ],
    "58": [
      {
        "id": 58,
        "text": "Our friend",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 3,
        "sentNum": 10,
        "position": [
          10,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 60,
        "text": "no ordinary scofflaw but a federal judge who has just lost his wife",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 4,
        "endIndex": 17,
        "sentNum": 10,
        "position": [
          10,
          3
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 61,
        "text": "no ordinary scofflaw",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 4,
        "endIndex": 7,
        "sentNum": 10,
        "position": [
          10,
          4
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 64,
        "text": "his",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 15,
        "endIndex": 16,
        "sentNum": 10,
        "position": [
          10,
          7
        ],
        "isRepresentativeMention": False
      }
    ],
    "59": [
      {
        "id": 59,
        "text": "Our",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 1,
        "endIndex": 2,
        "sentNum": 10,
        "position": [
          10,
          2
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 70,
        "text": "we",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 5,
        "endIndex": 6,
        "sentNum": 13,
        "position": [
          13,
          2
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 73,
        "text": "our",
        "type": "PRONOMINAL",
        "number": "PLURAL",
        "gender": "UNKNOWN",
        "animacy": "ANIMATE",
        "startIndex": 12,
        "endIndex": 13,
        "sentNum": 13,
        "position": [
          13,
          5
        ],
        "isRepresentativeMention": False
      }
    ],
    "62": [
      {
        "id": 62,
        "text": "a federal judge who has just lost his wife",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 8,
        "endIndex": 17,
        "sentNum": 10,
        "position": [
          10,
          5
        ],
        "isRepresentativeMention": True
      },
      {
        "id": 76,
        "text": "this “judge”",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 3,
        "endIndex": 7,
        "sentNum": 15,
        "position": [
          15,
          1
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 78,
        "text": "his",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 11,
        "endIndex": 12,
        "sentNum": 15,
        "position": [
          15,
          3
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 83,
        "text": "him",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 12,
        "endIndex": 13,
        "sentNum": 16,
        "position": [
          16,
          4
        ],
        "isRepresentativeMention": False
      },
      {
        "id": 85,
        "text": "his",
        "type": "PRONOMINAL",
        "number": "SINGULAR",
        "gender": "MALE",
        "animacy": "ANIMATE",
        "startIndex": 16,
        "endIndex": 17,
        "sentNum": 16,
        "position": [
          16,
          6
        ],
        "isRepresentativeMention": False
      }
    ],
    "63": [
      {
        "id": 63,
        "text": "his wife",
        "type": "NOMINAL",
        "number": "SINGULAR",
        "gender": "FEMALE",
        "animacy": "ANIMATE",
        "startIndex": 15,
        "endIndex": 17,
        "sentNum": 10,
        "position": [
          10,
          6
        ],
        "isRepresentativeMention": True
      }
    ]
  }
)


print one_sentence.untokenize()
print one_sentence.caveman()
print one_sentence.event_only()