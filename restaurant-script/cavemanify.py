#!usr/bin/env python
import json
import uuid
import codecs

parsed_documents = ['documents/dinnersfromhell-document-' + "%03d" % (i,) + '.txt.json' for i in range(20)]

documents = []

for filename in parsed_documents:
	f = open(filename, 'r')
	filestring = f.read()
	f.close()

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
	for key in corefs.keys():
		coref = corefs[key]
		chain = []
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
					# print 'chain link:',; print chain_link
					# print
			# first = False
		# print '--------'
		chains.append(chain)

	docstring = '\n'.join(
		[
			'<DOCNAME>' + filename,
			'<UUID>' + str(uuid.uuid4())
		] + map(lambda chain: ' '.join(chain), chains))

	documents.append(docstring)

w = codecs.open('restaurants_train_20docs', 'w', encoding='utf8')
w.write('\n\n'.join(documents))
w.close()


# <DOCNAME>NYT_ENG_19940731.0217
# <UUID>37371451-91bb-4c23-9cc2-ee47f3e82b15
# space-separated chains, one chain per line
# e.g. visit->dobj live->prep_in get->prep_in do->nsubj be->nsubj 