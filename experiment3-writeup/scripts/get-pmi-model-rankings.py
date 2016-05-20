#!/usr/bin/env python

import pickle
import codecs, json
from nltk.tree import Tree
import os
from nltk.corpus import wordnet as wn
import csv
import erin_nachos

WARNINGS = False
RUN_ALL = False

documents_directory = '../../restaurant-script/documents'
training_corpora_directory = '../data/training-corpora'
experiment_results_file = '../data/experiment3.csv'

def warn(msg):
  if WARNINGS:
    print msg

def main():
  ## collect the set of documents in the experiment

  cloze_task_tags = pickle.load(open('tasks.p', 'rb')).keys()
  documents = [t[0] for t in cloze_task_tags]
  documents = list(set(documents))

  ## for each document:
  for document in documents:

  ##   * create a version of the restaurant blogs corpus
  ##     with that document left out
    if RUN_ALL:
      ## a very very slow function:
      create_corpus(exclude=document)
      warn("""WARNING 23: oops, there are capital letters in these corpora and they're not lemmatized!!""")

  ##   * compress the corpus
      corpus_filename = training_corpora_directory + "/corpus-excluding-" + document
      os.system("gzip " + corpus_filename)
  ##   * collect the set of cloze tasks for that document

      response_data = parse_responses()
      write_cloze_tests(document, cloze_task_tags, response_data[document])

  ##        * for each generated cloze task (see arrows in write_cloze_tests):
    chains = unique([t[1] for t in cloze_task_tags if t[0]==document])
    for chain in chains:
      for cloze_index in unique([t[2] for t in cloze_task_tags if t[0]==document and t[1]==chain]):
  ##          * run the PMI model to get the ranking of that event
        for exactness in ['exact', 'syns']:
          for source in ['actual', 'response']:
            cloze_test_file = '../data/cloze-tests/cloze-for-' + document + '-' + source + '-' + exactness
            training_file = '../data/training-corpora/corpus-excluding-' + document + '.gz'
  ##        * find and RECORD the ranking
            erin_nachos.nachos(cloze_file=cloze_test_file, training_file=training_file, docmin=3, threshold=10, subjobj=True, coref='all')

def parse_responses():
  experiment_results_file_with_caveman = experiment_results_file[:-4] + '-with-caveman-parsing.csv'

  if RUN_ALL:
    new_rows = []
    for row in csv.DictReader(open(experiment_results_file, 'rb')):
      response = row['response']
      os.system('wget --post-data "' + response + '" \'localhost:9000/?properties={"annotators": "tokenize,ssplit,pos,lemma,parse,sentiment", "outputFormat": "json"}\' -O - > tmp.json')
      parsed_response = json.loads(open('tmp.json', 'rb').read())
      caveman = Caveman(parsed_response['sentences'][0])
      row['response.caveman'] = caveman.speak()
      row['response.main.verb'] = caveman.verb
      new_rows.append(row)

    w = csv.DictWriter(open(experiment_results_file_with_caveman, 'wb'), new_rows[0].keys())
    w.writeheader()
    w.writerows(new_rows)

  ## for each document, make an object with keys for each chain, with keys for each cloze task
  ## with a list of people's responses on that item.

  response_data = {}

  for row in csv.DictReader(open(experiment_results_file_with_caveman, 'rb')):
    doc = row['document']
    chain = row['chain']
    cloze = row['clozeIndex']
    response_main_verb = row['response.main.verb']
    if doc not in response_data:
      response_data[doc] = {}
    doc_data = response_data[doc]
    if chain not in doc_data:
      doc_data[chain] = {}
    chain_data = doc_data[chain]
    if cloze not in chain_data:
      chain_data[cloze] = []
    cloze_data = chain_data[cloze]
    cloze_data.append(response_main_verb)
  return response_data


def get_docfilename(d):
  if type(d) is not str and type(d) is not unicode:
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
  def get(self, lookup):
    if type(lookup) is int:
      ## force integers to Indexes
      lookup = Index(lookup, type='good')
    if isinstance(lookup, Index):
      index = lookup
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
    else:
      ## search for a dependency of that type
      candidates = [d for d in self.list if lookup(d)]
      return candidates
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

def get_event_chains(document):
  filename = get_docfilename(document)

  ## read the corenlp parsed document from the documents directory
  nlp_data = json.loads(codecs.open(filename, 'r', encoding='utf-8').read())
  sentences = nlp_data['sentences']    ## collect a list of chains in this document

  document_chains = {}

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
        event_word = sentence['tokens'][governor.index.good]['lemma'].lower()
        event = (event_word, deptype)

        event_string = '->'.join(event)
        events.append(event_string)
    event_string = ' '.join(events)
    document_chains[chain] = event_string

  return document_chains

def create_corpus(exclude='000'):
  ## this function is hella slow
  print(exclude)

  ## collect the corpus, which will be divided into document sections
  document_sections = []

  ## for each document that's not the excluded document,
  other_docs = [i for i in range(274) if i!=int(exclude)]
  for otherdoc in other_docs:

    filename = get_docfilename(otherdoc)

    ## write some header lines, like `nachos` expects
    doctag = "<DOCNAME>" + filename
    docUUIDtag = "<UUID>" #ignore this for now

    document_chain_dict = get_event_chains(otherdoc)
    document_chains = []
    for chain in document_chain_dict:
      document_chains.append(document_chain_dict[chain])

    document_section = '\n'.join([doctag, docUUIDtag] + document_chains)
    document_sections.append(document_section)

  corpus_filename = training_corpora_directory + "/corpus-excluding-" + exclude
  codecs.open(corpus_filename, 'wb', 'utf-8').write("\n\n".join(document_sections))

def make_cloze_test(document, event_chain, cloze_index, answer=None):
    cloze = [event_chain[i] for i in range(len(event_chain)) if i!=int(cloze_index)]

    orig_answer, orig_role = event_chain[int(cloze_index)].split('->')

    if not answer:
      answer = orig_answer

    ## replace with new answer
    new_answer = answer + '->' + orig_role

  ##  -->   * create the correct cloze task for the PMI model
    cloze_test = "\n".join([
      "<DOCNAME>" + document,
      "<CHAIN> len:" + str(len(event_chain)),
      "<TEST>",
      "<ANSWER> " + new_answer,
      "<INSERT_INDEX>" + cloze_index,
      "<CLOZE>" + ' '.join(cloze)
      ])

    return cloze_test

class Caveman:
  def __init__(self, sentence, focal_predicate=None):
    ## we might want a focal predicate, so we could get multiple caveman objects from one sentence
    # print ' '.join([t['word'] for t in sentence['tokens']])

    self.verb = None
    self.subj = None
    self.obj = None
    self.prepositions = []
    self.voice = 'unknown'

    dependencies = Dependencies(sentence['collapsed-dependencies'])
    ## start from root
    root_candidates = dependencies.get(lambda d: d.type=='ROOT')
    if len(root_candidates) != 1:
      print """WARNING 517: I think ROOT should be the type of exactly one dependency..."""
      print [d.str for d in root_candidates]
    root = root_candidates[0]
    ## might not actually be a verb (could be adjectival predicate):
    self.verb = sentence['tokens'][root.index.good]['lemma']

    ## pick out any conj relations from root. these are probably separate event predicates
    conj_candidates = dependencies.get(lambda d: d.type[:4]=='conj')
    for conj in conj_candidates:
      print """TO DO 492: add conj-linked events"""
      print ' '.join([t['word'] for t in sentence['tokens']])
      print conj.str

    ## for each event predicate:
    ##    see if there's an nsubj or nsubjpass

    nsubj_candidates = dependencies.get(lambda d: d.type=='nsubj' and d.governor.good==root.index.good)
    if len(nsubj_candidates) > 1:
      print """WARNING 517: I think nsubj should be the type of at most one dependency with governor ROOT..."""
      print [d.str for d in nsubj_candidates]

    nsubjpass_candidates = dependencies.get(lambda d: d.type=='nsubjpass' and d.governor.good==root.index.good)
    if len(nsubjpass_candidates) > 1:
      print """WARNING 5143: I think nsubjpass should be the type of at most one dependency with governor ROOT..."""
      print [d.str for d in nsubjpass_candidates]

    if len(nsubjpass_candidates)>0 and len(nsubj_candidates)>0:
      print """WARNING 2894: Why does this predicate have both an active and passive subject???!!!!"""
      print [d.str for d in nsubjpass_candidates]
      print [d.str for d in nsubj_candidates]

    if len(nsubjpass_candidates)>0:
    ##    if nsubjpass:
    ##        keep exact word of event predicate
      subj_index = nsubjpass_candidates[0].index
      self.subj = sentence['tokens'][subj_index.good]['lemma']
      self.voice = 'passive'
      self.verb = sentence['tokens'][root.index.good]['lemma']
    elif len(nsubj_candidates)>0:
    ##    if nsubj:
    ##        lemmatize event predicate
      subj_index = nsubj_candidates[0].index
      self.subj = sentence['tokens'][subj_index.good]['lemma']
      self.voice = 'active'
      self.verb = sentence['tokens'][root.index.good]['lemma']

    ##        see if there's a dobj (there shouldn't be in a passive sentence)
    dobj_candidates = dependencies.get(lambda d: d.type=='dobj' and d.governor.good==root.index.good)
    if len(dobj_candidates) > 1:
      print """WARNING 514343: I think a predicate should have at most one direct object..."""
    if len(dobj_candidates)>0:
      self.obj = sentence['tokens'][dobj_candidates[0].index.good]['lemma']
      if self.voice == 'passive':
        print """WARNING 472: Why does this passive sentence have a direct object?"""

    ##    see if there's an nmod:xxx from the predicate. if so, grab xxx and store the PP
    prep_candidates = dependencies.get(lambda d: d.type[:4]=='nmod' and d.governor.good==root.index.good)
    for prep in prep_candidates:
      prep_type = prep.type[5:]
      prep_word = sentence['tokens'][prep.index.good]['lemma']
      self.prepositions.append((prep_type, prep_word))

    ##    (to do: note that ccomp relations like "I said there was a storm" will be left out)

  def speak(self):
    print self.subj
    print self.verb
    print self.obj
    print self.prepositions
    elements = [self.subj, self.verb, self.obj] + [' '.join(p) for p in self.prepositions]
    return ' '.join([e for e in elements if e])

def write_cloze_tests(document, cloze_task_tags, document_data):

  cloze_test_filename_actual_exact = '../data/cloze-tests/cloze-for-' + document + '-actual-exact'
  cloze_test_filename_actual_syns = '../data/cloze-tests/cloze-for-' + document + '-actual-syns'
  cloze_test_filename_response_exact = '../data/cloze-tests/cloze-for-' + document + '-response-exact'
  cloze_test_filename_response_syns = '../data/cloze-tests/cloze-for-' + document + '-response-syns'

  event_chains = get_event_chains(document)
  actual_exact_cloze_tests = []
  actual_syns_cloze_tests = []
  response_exact_cloze_tests = []
  response_syns_cloze_tests = []

  ##   * for each cloze task:
  for task in [t for t in cloze_task_tags if t[0]==document]:
    doc, chain, cloze_index = task
    taks_data = document_data[chain][cloze_index]
    event_chain = event_chains[chain].split(" ")

    actual_exact_cloze_test = make_cloze_test(document, event_chain, cloze_index)
    actual_exact_cloze_tests.append(actual_exact_cloze_test)
    actual_syns_cloze_tests.append(actual_exact_cloze_test)

  ##        * collect the synonyms of the first synset in wordnet
  ##          of the main predicate
    original_answer, original_role = event_chain[int(cloze_index)].split('->')

    synsets = wn.synsets(original_answer)
    if len(synsets) > 0:
      synonyms = [str(lemma.name()) for lemma in synsets[0].lemmas()]
      for synonym in synonyms:
  ##        * for each synonym of the correct predicate:
  ##  -->       * create a cloze task for the PMI model
        syn_cloze_test = make_cloze_test(document, event_chain, cloze_index, answer=synonym)
        actual_syns_cloze_tests.append(syn_cloze_test)

  ##        * collect the main predicates of the responses that
  ##          people gave
  ##        * for each predicate that people gave in their responses:
        for response_verb in taks_data:
  ##  -->       * create a cloze task for the PMI model
          response_exact_cloze_tests.append(make_cloze_test(document, event_chain, cloze_index, answer=response_verb))
  ##            * collect the synonyms of the first synset in wordnet
          synsets = wn.synsets(response_verb)
          if len(synsets) > 0:
            synonyms = [str(lemma.name()) for lemma in synsets[0].lemmas()]
            for synonym in synonyms:
  ##            * for each synonym of the response predicates:
  ##  -->           * create a cloze task for the PMI model
              response_syns_cloze_tests.append(make_cloze_test(document, event_chain, cloze_index, answer=synonym))
  
  codecs.open(cloze_test_filename_actual_exact, 'wb', 'utf-8').write("\n\n".join(unique(actual_exact_cloze_tests)))
  codecs.open(cloze_test_filename_actual_syns, 'wb', 'utf-8').write("\n\n".join(unique(actual_syns_cloze_tests)))
  codecs.open(cloze_test_filename_response_exact, 'wb', 'utf-8').write("\n\n".join(unique(response_exact_cloze_tests)))
  codecs.open(cloze_test_filename_response_syns, 'wb', 'utf-8').write("\n\n".join(unique(response_syns_cloze_tests)))

def unique(lst):
  return list(set(lst))

if __name__ == "__main__":
    main()