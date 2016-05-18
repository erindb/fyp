#!/usr/bin/env python

## collect the set of documents in the experiment

## for each document:
##   * create versions of the restaurant blogs corpus
##     with those documents left out
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