#!/usr/bin/env python

import pickle
import codecs, json
documents_directory = '../../restaurant-script/documents'
training_corpora_directory = '../data/training-corpora'
from nltk.tree import Tree

WARNINGS = False

def warn(msg):
  if WARNINGS:
    print msg

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
      warn("""
            WARNING 21345: I'm not sure if the indices
                           we're within should ever be identical
            """)
      return a.good == self.good and self.good == b.good
  def increment(self, i):
    return Index(self.good + i, type='good')

class Dep:
  def __init__(self, dependency):
    self.type = dependency['dep']
    self.index = Index(dependency['dependent'])
    self.governor = Index(dependency['governor'])
    self.governorGloss = dependency['governorGloss']
    self.word = dependency['dependentGloss']
    self.str = json.dumps(dependency)

class Dependencies:
  def __init__(self, dependencies):
    self.list = [Dep(d) for d in dependencies]
  def within(self, startIndex, endIndex):
    return [d for d in self.list if d.index.within(startIndex, endIndex)]
  def get(self, index):
    candidates = [d for d in self.list if d.index.good == index.good]
    if len(candidates) > 0:
      if len(candidates) > 1:
        warn("WARNING 6243: There are multiple candidates. " + \
              "I'm taking the *first* of " + ", ".join([str(c.index.good) for c in candidates]))
      return candidates[0]
    else:
      print """
            ERROR 6: I'm not sure what to do if there are no candidates
            """
  def str(self):
    return [d.str for d in self.list]

def index_at_position(tree, position):
  noun_index_candidates = [
    Index(i, type='good') for i in range(len(tree.leaves())) if \
    tree.leaf_treeposition(i)==position
  ]
  if len(noun_index_candidates)!=1:
    print tree.leaves()
    print position
    print """
    ERROR 345: exactly one index in the tree should have that position!
    """
  else:
    return noun_index_candidates[0]

def extract_head_noun_index(parsestring, startIndex, endIndex):
  ## if the referent is a long phrase, try to find the head noun
  parse = Tree.fromstring(parsestring)
  phrase_position = parse.treeposition_spanning_leaves(startIndex.good,
                                                       endIndex.good)
  phrase = parse[phrase_position]
  if type(phrase) is unicode:
    return index_at_position(parse, phrase_position)
  # ## we need to know where in the sentence the head noun occurred
  # ## so don't loose the information about the treeposition of the noun!
  subtree_direct_indices = [i for i in range(len(phrase)) if type(phrase[i]) is Tree]
  noun_positions = [phrase_position + (i, 0,) for i in subtree_direct_indices if (phrase[i].label() in ['NN', 'NNS', 'NNP'])]
  noun_indices = [index_at_position(parse, p) for p in noun_positions]
  if len(noun_indices)==1:
    return noun_indices[0]
  else:
    noun_phrase_positions = [phrase_position + (i,) for i in subtree_direct_indices if phrase[i].label()=='NP']
    if len(noun_phrase_positions)>0:
      if len(noun_phrase_positions)!=1:
        warn("WARNING 45: there were multiple top-level noun phrases. " + \
              "I'm returning the head noun of the *first*")
      for noun_phrase_pos in noun_phrase_positions:
        noun_phrase = parse[noun_phrase_pos]
        np_start_position = noun_phrase_pos + noun_phrase.leaf_treeposition(0)
        np_start = index_at_position(parse, np_start_position)
        np_end_in_np = noun_phrase.leaf_treeposition(len(noun_phrase.leaves())-1)
        np_end_position = noun_phrase_pos + noun_phrase.leaf_treeposition(len(noun_phrase.leaves())-1)
        np_end = index_at_position(parse, np_end_position).increment(1)
        return extract_head_noun_index(parsestring, np_start, np_end)
    else:
      subtree_positions = [tp for tp in phrase.treepositions() if type(phrase[tp]) is Tree]
      noun_positions = [tp + (0,) for tp in subtree_positions if (phrase[tp].label() in ['NN', 'NNS', 'NNP'])]
      if len(noun_positions) > 0:
        if len(noun_positions) != 1:
          warn("WARNING 45243: there were multiple noun phrases. " + \
                "I'm returning the *first* of " + " ".join([phrase[tp] for tp in noun_positions]))
        return index_at_position(parse, phrase_position + noun_positions[0])
      else:
        warn("WARNING 1243: the phrase \"" + ' '.join(phrase.leaves()) + "\" contains no noun." + \
              " I'm taking the last word in the phrase.")
        return index_at_position(parse, phrase_position + phrase.leaf_treeposition(len(phrase.leaves())-1))

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

        if referent.governorGloss != "ROOT":
          ## figure out the governor of the referent
          governor = dependencies.get(referent.governor)
          ## and the type of that dependency
          deptype = referent.type
          ## to create the event
          event = (governor.word, deptype)

          event_string = '->'.join(event)
          events.append(event_string)
      event_string = ' '.join(events)
      document_chains.append(event_string)
    document_section = '\n'.join([doctag, docUUIDtag] + document_chains)
    document_sections.append(document_section)

  corpus_filename = training_corpora_directory + "/corpus-excluding-" + exclude
  codecs.open(corpus_filename, 'wb', 'utf-8').write("\n\n".join(document_sections))

if __name__ == "__main__":
    main()