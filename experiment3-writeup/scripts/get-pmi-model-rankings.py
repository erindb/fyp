#!/usr/bin/env python

import pickle
import codecs, json
documents_directory = '../../restaurant-script/documents'
from nltk.tree import Tree

def main():
  ## collect the set of documents in the experiment

  cloze_task_tags = pickle.load(open('tasks.p', 'rb')).keys()
  documents = [t[0] for t in cloze_task_tags]

  ## for each document:
  for document in documents:

  ##   * create a version of the restaurant blogs corpus
  ##     with that document left out
    create_corpus(exclude=document)

  ##   * collect the set of cloze tasks for that document

  ##   * for each cloze task:
  ##  -->   * create the correct cloze task for the PMI model
  ##        * collect the synonyms of the first synset in wordnet
  ##          of the main predicate
  ##        * for each synonym of the correct predicate:
  ##  -->       * create a cloze task for the PMI model
  ##        * collect the main predicates of the responses that
  ##          people gave
  ##        * for each predicate that people gave in their responses:
  ##  -->       * create a cloze task for the PMI model
  ##            * collect the synonyms of the first synset in wordnet
  ##            * for each synonym of the response predicates:
  ##  -->           * create a cloze task for the PMI model
  ##        * for each generated cloze task (see arrows above):
  ##          * run the PMI model to get the ranking of that event
  ##        * find and RECORD the max ranking for the correct response
  ##        * find and RECORD the max ranking for the highest-ranking
  ##          human response

def get_docfilename(d):
  if type(d) is not str:
    d = "%03d" % (d,)
  return documents_directory + '/dinnersfromhell-document-' + \
         d + '.txt.json'

class Index:
  def __init__(self, i, type='bad'):
    if type=='bad':
      self.bad = i
      self.good = int(i)-1
    else:
      self.bad = str(i+1)
      self.good = i
  def within(self, a, b):
    if a.good < b.good:
      return a.good <= self.good and self.good < b.good
    elif b.good < a.good:
      return b.good <= self.good and self.good < a.good
    else:
      print """
            WARNING 21345: I'm not sure if the indices
                           we're within should ever be identical
            """
      return a.good == self.good and self.good == b.good

class Dep:
  def __init__(self, dependency):
    self.type = dependency['dep']
    self.index = Index(dependency['dependent'])
    self.governor = Index(dependency['governor'])
    self.governorGloss = dependency['governorGloss']
    self.word = dependency['dependentGloss']

class Dependencies:
  def __init__(self, dependencies):
    self.list = [Dep(d) for d in dependencies]
  def within(self, startIndex, endIndex):
    return [d for d in self.list if d.index.within(startIndex, endIndex)]
  def get(self, index):
    candidates = [d for d in self.list if d.index.good == index.good]
    if len(candidates) == 1:
      return candidates[0]
    else:
      print """
            TODO 6: I'm not sure what to do if there are no/multiple candidates
            """

def extract_head_noun_index(parsestring, startIndex, endIndex):
  ## if the referent is a long phrase, try to find the head noun
  parse = Tree.fromstring(parsestring)
  phrase_position = parse.treeposition_spanning_leaves(startIndex.good,
                                                       endIndex.good)
  phrase = parse[phrase_position]
  noun_indices = []
  ## we need to know where in the sentence the head noun occurred
  ## so don't loose the information about the treeposition of the noun!
  for treeposition in phrase.treepositions():
    if len(treeposition)==1:
      subtree = phrase[treeposition]
      if subtree.label()=='NN':
        noun = subtree[0]
        noun_position = phrase_position + treeposition + (0,)
        noun_index_candidates = [
          Index(i, type='good') for i in range(len(parse.leaves())) if \
          parse.leaf_treeposition(i)==noun_position
        ]
        if len(noun_index_candidates)!=1:
          print """
          ERROR 345: exactly one index in the tree should have that position!
          """
        noun_indices.append(noun_index_candidates[0])

  if len(noun_indices)==1:
    return noun_indices[0]
  else:
    print phrase.pos()
    print """
          TODO 1243: not sure what to do when referent phrase contains
          no/multiple nouns at the highest level
          """

def create_corpus(exclude='000'):

  ## collect the corpus, which will be divided into document sections
  document_sections = []

  ## for each document that's not the excluded document,
  other_docs = [get_docfilename(i) for i in range(274) if i!=int(exclude)]
  for filename in other_docs:

    ## read the corenlp parsed document from the documents directory
    nlp_data = json.loads(codecs.open(filename, 'r', encoding='utf-8').read())
    sentences = nlp_data['sentences']

    ## write some header lines, like `nachos` expects
    doctag = "<DOCNAME>" + filename
    docUUIDtag = "<UUID>" #ignore this for now

    ## collect a list of chains in this document
    document_chains = []

    ## for each coreference chain in the document,
    for chain in nlp_data['corefs']:

      ## collect a set of events where that referent is mentioned
      events = []
      references = nlp_data['corefs'][chain]

      ## for each mention of that referent,
      for mention in references:

        ## figure out where that mention happened in the document
        endIndex = Index(mention['endIndex'])
        startIndex = Index(mention['startIndex'])
        sentNum = Index(mention['sentNum'])

        ## then look up that sentence in the parsed sentences
        sentence = sentences[sentNum.good]

        ## figure out what element in the dependency parse corresponds
        ## to this referent
        dependencies = Dependencies(sentence['collapsed-dependencies'])
        possibly_referent = dependencies.within(startIndex, endIndex)
                             
        words = [d.word for d in possibly_referent]
        if len(words)==1:
          referent = possibly_referent[0]
        else:
          noun_index = extract_head_noun_index(sentence['parse'], startIndex,
                                               endIndex)
          referent = dependencies.get(noun_index)

        ## figure out the governor of the referent
        governor = dependencies.get(referent.governor)
        ## and the type of that dependency
        deptype = governor.type
        ## to create the event
        event = (governor.word, deptype)

        event_string = '->'.join(event)
        events.append(event_string)
      event_string = ' '.join(events)
      document_chains.append(event_string)
    document_section = '\n'.join([doctag, docUUIDtag] + document_chains)
    document_sections.append(document_section)

if __name__ == "__main__":
    main()