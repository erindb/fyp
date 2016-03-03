#!usr/bin/env python
import json
import uuid
import codecs
import re
from nltk.tree import *

parsed_documents = ['documents/dinnersfromhell-document-' + "%03d" % (i,) + '.txt.json' for i in range(20)]

documents = []

for filename in parsed_documents:
	f = codecs.open(filename, 'r', encoding='utf-8')
	filestring = f.read()
	f.close()

	# for each document, record which [sentence, word] indices are cloze events?
	# color each chain independently
	# annotations = {}
	colors = [
		'indianred',
		'tomato',
		'coral',
		'chocolate',
		'orangered',
		'yellowgreen',
		'darkgreen',
		'olivedrab',
		'seagreen',
		'teal',
		'navy',
		'steelblue',
		'slateblue',
		'rebeccapurple',
		'purple',
		'orchid',
		'darkmagenta',
		'mediumvioletred',
		'magenta',
		'peru',
		'cadetblue',
		'darkcyan',
		'darkgoldenrod',
		'darkseagreen',
		'deepskyblue',
		'dodgerblue',
		'firebrick',
		'forestgreen',
		'hotpink',
		'green',
		'lightcoral',
		'lawngreen',
		'khaki',
		'lightsalmon',
		'blue',
		'mediumspringgreen',
		'palevioletred',
		'plum',
		'saddlebrown',
		'salmon',
		'sienna',
		'mediumvioletred',
		'purple',
		'blue',
		'seagreen',
		'limegreen',
		'yellow',
		'darkorange',
		'crimson',
		'deeppink'
	]
	# annotation: sentence index, word index, coref color (for each entity and verb head word)

	nlp_data = json.loads(filestring)
	# keys: corefs, sentences
	corefs = nlp_data['corefs']
	sentences = nlp_data['sentences']

	def print_tokens(sentence):
		print ' '.join(map(lambda x: x['originalText'], sentence['tokens']))
	def word(sentence, index):
		return filter(lambda x: x['index'] == index, sentence['tokens'])[0]

	# first = True
	chains = []
	for i in range(len(corefs.keys())):
		key = corefs.keys()[i]
		coref = corefs[key]
		# coref is set of coreferring entities
		color = ""
		# has its own color
		chain = []
		annotations = {}
		single_chain_annotations = []
		# print map(lambda x: x['text'], coref)
		for ref in coref:
			# if first:
				# print 'ref:',;  print ref['text']
				assert(ref['sentNum'] == ref['position'][0]) #check that i understand what these indices are
				sentence_index = ref['sentNum']-1 #sentences are 0-indexed
				index_in_sentence = ref['startIndex'] 
				sentence = sentences[sentence_index] #find the sentence with that reference
				# keys: tokens, index, basic-dependencies, parse, collapsed-dependencies, collapsed-ccprocessed-dependencies
				# print 'sentence:',; print_tokens(sentence)
				dependencies = sentence['collapsed-ccprocessed-dependencies']
				# print '---dependencies---'
				# print dependencies
				# not sure which kind of dependencies i actually want...
				ref_dep = filter(lambda x: x['dependent'] == index_in_sentence, dependencies)[0]
				# print ref_dep
				# reference entity is the dependent, 'dep' is its role, and 'governorGloss' is its event
				if ref_dep['governor'] != 0:
					event_verb_index = ref_dep['governor']
					event_verb = word(sentence, event_verb_index)['lemma']
					entity_role = ref_dep['dep']
					chain_link = event_verb + '->' + entity_role
					chain.append(chain_link)
					# single_chain_annotations.append({'sentence_index': sentence_index, 'event': event_verb_index, 'color': color})
					if entity_role in ['nsubj', 'dobj', 'nsubjpass', 'nmod:poss']:
						tree = Tree.fromstring(sentence['parse'])
						# posified_tokens = re.findall('\([^() \n\t]+ [^() \n\t]+\)', parse)
						# posified_verb = '(' + pos + ' ' + originalText + ')'
						# verb_matching_tokens = map(lambda x: x==posified_verb, posified_tokens)
						# matching_verb_phrases = re.findall(posified_verb + '[ \n\t]*(\([^() \n\t]+ [^() \n\t]+\))*\)', parse)
						# verb_phrase_length = matching_verb_phrases
						verb_head_index = event_verb_index-1
						phrase_leaves = tree[tree.leaf_treeposition(verb_head_index)[:-2]].leaves()
						upper = -1
						lower = len(sentence)+10
						i = 0
						while verb_head_index > upper:
							upper = tree.leaves().index(phrase_leaves[-1], i)
							i+=1
						i = 0
						while verb_head_index < lower:
							lower = tree.leaves().index(phrase_leaves[0], i)
							i+=1
						assert(verb_head_index >= lower)
						assert(verb_head_index <= upper)
						verb_phrase_end_index = upper + 1
						single_chain_annotations.append({
							'sentence_index': sentence_index,
							'entity_start': index_in_sentence -1,
							'entity_end': ref['endIndex'] - 1,
							'verb_head_index': verb_head_index,
							'verb_end_index': verb_phrase_end_index
						})
					# print 'chain link:',; print chain_link
					# print
			# first = False
		# print '--------'
		chains.append(chain)
		if len(single_chain_annotations)>1:
			color = colors.pop()
			for annotation in single_chain_annotations:
				s = annotation['sentence_index']
				entity_start = annotation['entity_start']
				entity_end = annotation['entity_end']
				if s not in annotations.keys():
					annotations[s] = {}
				for w in range(annotation['verb_head_index'], annotation['verb_end_index']):
					annotations[s][w] = 'steelblue'
				for w in range(entity_start, entity_end):
					annotations[s][w] = 'navy'

			html_body = []
			cloze_sentences = list(set(map(lambda x: x['sentence_index'], single_chain_annotations)))
			cloze_verb_heads = list(set(map(lambda x: x['verb_head_index'], single_chain_annotations)))
			cloze_verb_tails = list(set(map(lambda x: x['verb_end_index'] - 1, single_chain_annotations)))
			cloze_body = []
			cloze_index = 0
			for s in range(len(sentences)):
				sentence = sentences[s]['tokens']
				for w in range(len(sentence)):
					lala_word = sentence[w]
					wordform = lala_word['originalText']
					if (s) in annotations.keys():
						if (w) in annotations[s]:
							html_body.append('<b><font color="' + annotations[s][w] + '">' + \
								wordform + '</font></b>')
						else:
							html_body.append(wordform)
					else:
						html_body.append(wordform)
					if s in cloze_sentences:
						if w in cloze_verb_heads:
							cloze_body.append('<span class="cloze" id="cloze_' + str(cloze_index) + '">')
						cloze_body.append(wordform)
						if w in cloze_verb_tails:
							cloze_body.append('</span>')
							cloze_index += 1
			html_filename = filename.split('.')[0] + '_' + str(len(chains)) + '.html'
			w = codecs.open(html_filename, 'w', encoding='utf-8')
			w.write('<html><head><meta charset="utf-8"></head><body>' + ' '.join(html_body) + '</body></html>')
			w.close()
			cloze_filename = filename.split('.')[0] + '_' + str(len(chains)) + '_cloze.html'
			w = codecs.open(cloze_filename, 'w', encoding='utf-8')
			w.write('<html><head><meta charset="utf-8"></head><script src="../jquery-2.2.0.min.js"></script><body>' + ' '.join(cloze_body) + '<script>function cloze(i) { $("#cloze_" + i).hide(); $("#cloze_" + i).before("<input type=\'text\'></input>") }</script></body></html>')
			w.close()

	# html_body = []
	# for s in range(len(sentences)):
	# 	sentence = sentences[s]['tokens']
	# 	for w in range(len(sentence)):
	# 		word = sentence[w]
	# 		wordform = word['originalText']
	# 		if (s) in annotations.keys():
	# 			if (w) in annotations[s]:
	# 				html_body.append('<b><font color="' + annotations[s][w] + '">' + \
	# 					wordform + '</font></b>')
	# 			else:
	# 				html_body.append(wordform)
	# 		else:
	# 			html_body.append(wordform)
	# html_filename = filename.split('.')[0] + '.html'
	# w = codecs.open(html_filename, 'w', encoding='utf-8')
	# w.write('<html><head><meta charset="utf-8"></head><body>' + ' '.join(html_body) + '</body></html>')
	# w.close()

	docstring = '\n'.join(
		[
			'<DOCNAME>' + filename,
			'<UUID>' + str(uuid.uuid4())
		] + map(lambda chain: ' '.join(chain), chains))

	documents.append(docstring)

w = codecs.open('restaurants_train_100docs', 'w', encoding='utf-8')
w.write('\n\n'.join(documents))
w.close()


# <DOCNAME>NYT_ENG_19940731.0217
# <UUID>37371451-91bb-4c23-9cc2-ee47f3e82b15
# space-separated chains, one chain per line
# e.g. visit->dobj live->prep_in get->prep_in do->nsubj be->nsubj 