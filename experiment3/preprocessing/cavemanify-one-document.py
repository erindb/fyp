#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

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
    return []

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
    negation_indices = findDepIndex(
      self.dependencies,
      governorIndex=head_verb_index,
      depType='neg')
    self.negation = False
    if negation_indices:
      self.negation = True

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

docIndex = '022'
with open('../../restaurant-script/documents/dinnersfromhell-document-' + docIndex +'.txt.json', 'r') as f:
  jsonFile = f.read()
nlpJSON = json.loads(jsonFile)
sentences = nlpJSON['sentences']
corefs = nlpJSON['corefs']
for sentence in sentences:
  one_sentence = Sentence(sentence, corefs)
  print one_sentence.untokenize()
  print one_sentence.caveman()
  print one_sentence.event_only()