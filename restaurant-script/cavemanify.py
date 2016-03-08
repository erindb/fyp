#!usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
import codecs
import re
from nltk.tree import *

parsed_documents = ['documents/dinnersfromhell-document-' + "%03d" % (i,) + '.txt.json' for i in range(100)]

documents = []

cloze_chain_lengths = {}

def within(c, a, b):
	return (c>=a) & (c<b)

def without(c, a, b):
	return not within(c, a, b)

def cleanup_parsed_and_processed_text(text):
	return text.replace(u" ’s", "'s").replace(u" n’t", "n't").replace(" ,", ",").replace(" .", ".").replace(" ?", "?").replace(u"“ ", '"').replace(u" ”", '"').replace("( ", "(").replace(" )", ")")

chain_divs = []

censor_list=['"4r5e"', '"5h1t"', '"5hit"', 'a55', 'anal', 'anus', 'ar5e', 'arrse', 'arse', 'ass', '"ass-fucker"', 'asses', 'assfucker', 'assfukka', 'asshole', 'assholes', 'asswhole', 'a_s_s', '"b!tch"', 'b00bs', 'b17ch', 'b1tch', 'ballbag', 'balls', 'ballsack', 'bastard', 'beastial', 'beastiality', 'bellend', 'bestial', 'bestiality', '"bi+ch"', 'biatch', 'bitch', 'bitcher', 'bitchers', 'bitches', 'bitchin', 'bitching', 'bloody', '"blow job"', 'blowjob', 'blowjobs', 'boiolas', 'bollock', 'bollok', 'boner', 'boob', 'boobs', 'booobs', 'boooobs', 'booooobs', 'booooooobs', 'breasts', 'buceta', 'bugger', 'bum', '"bunny fucker"', 'butt', 'butthole', 'buttmuch', 'buttplug', 'c0ck', 'c0cksucker', '"carpet muncher"', 'cawk', 'chink', 'cipa', 'cl1t', 'clit', 'clitoris', 'clits', 'cnut', 'cock', '"cock-sucker"', 'cockface', 'cockhead', 'cockmunch', 'cockmuncher', 'cocks', '"cocksuck "', '"cocksucked "', 'cocksucker', 'cocksucking', '"cocksucks "', 'cocksuka', 'cocksukka', 'cok', 'cokmuncher', 'coksucka', 'coon', 'cox', 'crap', 'cum', 'cummer', 'cumming', 'cums', 'cumshot', 'cunilingus', 'cunillingus', 'cunnilingus', 'cunt', '"cuntlick "', '"cuntlicker "', '"cuntlicking "', 'cunts', 'cyalis', 'cyberfuc', '"cyberfuck "', '"cyberfucked "', 'cyberfucker', 'cyberfuckers', '"cyberfucking "', 'd1ck', 'damn', 'dick', 'dickhead', 'dildo', 'dildos', 'dink', 'dinks', 'dirsa', 'dlck', '"dog-fucker"', 'doggin', 'dogging', 'donkeyribber', 'doosh', 'duche', 'dyke', 'ejaculate', 'ejaculated', '"ejaculates "', '"ejaculating "', 'ejaculatings', 'ejaculation', 'ejakulate', '"f u c k"', '"f u c k e r"', 'f4nny', 'fag', 'fagging', 'faggitt', 'faggot', 'faggs', 'fagot', 'fagots', 'fags', 'fanny', 'fannyflaps', 'fannyfucker', 'fanyy', 'fatass', 'fcuk', 'fcuker', 'fcuking', 'feck', 'fecker', 'felching', 'fellate', 'fellatio', '"fingerfuck "', '"fingerfucked "', '"fingerfucker "', 'fingerfuckers', '"fingerfucking "', '"fingerfucks "', 'fistfuck', '"fistfucked "', '"fistfucker "', '"fistfuckers "', '"fistfucking "', '"fistfuckings "', '"fistfucks "', 'flange', 'fook', 'fooker', 'fuck', 'fucka', 'fucked', 'fucker', 'fuckers', 'fuckhead', 'fuckheads', 'fuckin', 'fucking', 'fuckings', 'fuckingshitmotherfucker', '"fuckme "', 'fucks', 'fuckwhit', 'fuckwit', '"fudge packer"', 'fudgepacker', 'fuk', 'fuker', 'fukker', 'fukkin', 'fuks', 'fukwhit', 'fukwit', 'fux', 'fux0r', 'f_u_c_k', 'gangbang', '"gangbanged "', '"gangbangs "', 'gaylord', 'gaysex', 'goatse', 'God', '"god-dam"', '"god-damned"', 'goddamn', 'goddamned', '"hardcoresex "', 'hell', 'heshe', 'hoar', 'hoare', 'hoer', 'homo', 'hore', 'horniest', 'horny', 'hotsex', '"jack-off "', 'jackoff', 'jap', '"jerk-off "', 'jism', '"jiz "', '"jizm "', 'jizz', 'kawk', 'knob', 'knobead', 'knobed', 'knobend', 'knobhead', 'knobjocky', 'knobjokey', 'kock', 'kondum', 'kondums', 'kum', 'kummer', 'kumming', 'kums', 'kunilingus', '"l3i+ch"', 'l3itch', 'labia', 'lmfao', 'lust', 'lusting', 'm0f0', 'm0fo', 'm45terbate', 'ma5terb8', 'ma5terbate', 'masochist', '"master-bate"', 'masterb8', '"masterbat*"', 'masterbat3', 'masterbate', 'masterbation', 'masterbations', 'masturbate', '"mo-fo"', 'mof0', 'mofo', 'mothafuck', 'mothafucka', 'mothafuckas', 'mothafuckaz', '"mothafucked "', 'mothafucker', 'mothafuckers', 'mothafuckin', '"mothafucking "', 'mothafuckings', 'mothafucks', '"mother fucker"', 'motherfuck', 'motherfucked', 'motherfucker', 'motherfuckers', 'motherfuckin', 'motherfucking', 'motherfuckings', 'motherfuckka', 'motherfucks', 'muff', 'mutha', 'muthafecker', 'muthafuckker', 'muther', 'mutherfucker', 'n1gga', 'n1gger', 'nazi', 'nigg3r', 'nigg4h', 'nigga', 'niggah', 'niggas', 'niggaz', 'nigger', '"niggers "', 'nob', '"nob jokey"', 'nobhead', 'nobjocky', 'nobjokey', 'numbnuts', 'nutsack', '"orgasim "', '"orgasims "', 'orgasm', '"orgasms "', 'p0rn', 'pawn', 'pecker', 'penis', 'penisfucker', 'phonesex', 'phuck', 'phuk', 'phuked', 'phuking', 'phukked', 'phukking', 'phuks', 'phuq', 'pigfucker', 'pimpis', 'piss', 'pissed', 'pisser', 'pissers', '"pisses "', 'pissflaps', '"pissin "', 'pissing', '"pissoff "', 'poop', 'porn', 'porno', 'pornography', 'pornos', 'prick', '"pricks "', 'pron', 'pube', 'pusse', 'pussi', 'pussies', 'pussy', '"pussys "', 'rectum', 'retard', 'rimjaw', 'rimming', '"s hit"', '"s.o.b."', 'sadist', 'schlong', 'screwing', 'scroat', 'scrote', 'scrotum', 'semen', 'sex', '"sh!+"', '"sh!t"', 'sh1t', 'shag', 'shagger', 'shaggin', 'shagging', 'shemale', '"shi+"', 'shit', 'shitdick', 'shite', 'shited', 'shitey', 'shitfuck', 'shitfull', 'shithead', 'shiting', 'shitings', 'shits', 'shitted', 'shitter', '"shitters "', 'shitting', 'shittings', '"shitty "', 'skank', 'slut', 'sluts', 'smegma', 'smut', 'snatch', '"son-of-a-bitch"', 'spac', 'spunk', 's_h_i_t', 't1tt1e5', 't1tties', 'teets', 'teez', 'testical', 'testicle', 'tit', 'titfuck', 'tits', 'titt', 'tittie5', 'tittiefucker', 'titties', 'tittyfuck', 'tittywank', 'titwank', 'tosser', 'turd', 'tw4t', 'twat', 'twathead', 'twatty', 'twunt', 'twunter', 'v14gra', 'v1gra', 'vagina', 'viagra', 'vulva', 'w00se', 'wang', 'wank', 'wanker', 'wanky', 'whoar', 'whore', 'willies', 'willy', 'xrated', 'xxx']
# http://fffff.at/googles-official-list-of-bad-words/

for filename in parsed_documents:
	f = codecs.open(filename, 'r', encoding='utf-8')
	filestring = f.read()
	f.close()

	m = re.search('"(' + '|'.join(censor_list) + ')"', filestring)
	if not m:

		# document tags
		file_start = filename.split('.')[0]
		file_number = file_start.split('-')[2]

		nlp_data = json.loads(filestring)
		# keys: corefs, sentences
		corefs = nlp_data['corefs']
		sentences = nlp_data['sentences']

		def print_tokens(sentence):
			print ' '.join(map(lambda x: x['originalText'], sentence['tokens']))
		def word(sentence, corenlp_index):
			return filter(lambda x: x['index'] == corenlp_index-1, sentence['tokens'])[0]

		chains = []
		chain_index = 0
		for i in range(len(corefs.keys())):
			key = corefs.keys()[i]
			coref = corefs[key]
			# coref is set of coreferring entities
			chain = []
			#highlight entity and events in each chain in an html file for reference
			chain_sentence_indices = []
			chain_entity_starts = {}
			chain_entity_ends = {}
			chain_event_starts = {}
			chain_event_ends = {}
			for ref in coref:
				#check that i understand what these indices are
				assert(ref['sentNum'] == ref['position'][0])
				sentence_index = ref['sentNum']-1 #sentences are 0-indexed

				if not sentence_index in chain_sentence_indices:
					chain_sentence_indices.append(sentence_index)
					chain_entity_starts[sentence_index] = []
					chain_entity_ends[sentence_index] = []
					chain_event_starts[sentence_index] = []
					chain_event_ends[sentence_index] = []

				entity_start = ref['startIndex']-1
				entity_end = ref['endIndex']-1
				sentence = sentences[sentence_index] #find the sentence with that reference
				tree = Tree.fromstring(sentence['parse']) #get parse tree
				entity_tree = tree[tree.treeposition_spanning_leaves(entity_start, entity_end)] #get tree of noun phrase
				# keys: tokens, index, basic-dependencies, parse, collapsed-dependencies, collapsed-ccprocessed-dependencies
				dependencies = sentence['collapsed-ccprocessed-dependencies']
				# find dependency such that the dependent is in the noun phrase but the governor is outside the noun phrase
				all_entity_dependencies = filter(lambda d: within(d['dependent']-1, entity_start, entity_end) & \
					without(d['governor']-1, entity_start, entity_end), dependencies)
				# not sure which kind of dependencies i actually want...
				# maybe ['nsubj', 'dobj', 'nsubjpass', 'nmod:poss']
				entity_dependencies = filter(lambda d: d['dep'] in ['nsubj', 'dobj', 'nsubjpass', 'nmod:poss'], all_entity_dependencies)
				if len(entity_dependencies) > 0:
					for entity_dependency in entity_dependencies:
						# reference entity is the dependent, 'dep' is its role, and 'governorGloss' is its event

						entity_role = entity_dependency['dep']
						governor_index = entity_dependency['governor']-1
						governor_lemma = sentence['tokens'][governor_index]['lemma']
						chain_link = governor_lemma + '->' + entity_role
						chain.append(chain_link)

						event_phrase_leaves = tree[tree.leaf_treeposition(governor_index)[:-2]].leaves()
						upper = -1
						i = 0
						# multiple strings might match the phrase, but only one will contain the governor index
						while governor_index >= upper:
							upper = tree.leaves().index(event_phrase_leaves[-1], i) + 1
							lower = upper - len(event_phrase_leaves)
							i+=1
						assert(within(governor_index, lower, upper))

						if entity_start == lower:
							lower = entity_end
						chain_entity_starts[sentence_index].append(entity_start)
						chain_entity_ends[sentence_index].append(entity_end)
						chain_event_starts[sentence_index].append(lower)
						chain_event_ends[sentence_index].append(upper)

			chains.append(chain)

			# if (file_number == '009') and (chain_index==0):
			# 	print chain_entity_starts
			# 	print chain_entity_ends
			# 	print chain_event_starts
			# 	print chain_event_ends
			# 	for s in chain_sentence_indices:
			# 		print print_tokens(sentences[s])

			# don't report chains with length 1, cause you can't use them for finding sequences
			# (these might exist if some of the dependencies were ones that i'm not using)
			if len(chain) > 1:
				### write chain reference document with colors for entity references and events
				chain_reference_doc = [ '<!DOCTYPE html><html><head><meta charset="utf-8">\n' +
					'<title>Chain Reference Document' + file_number + ' Chain' + str(chain_index) + '</title></head>\n' +
					'<body><script src="jquery-2.2.0.min.js"></script>\n' ]
				### write cloze html for experiment
				cloze_div = ['<div class="chain document' + file_number + ' chain' + str(chain_index) + '"><p>']
				cloze_index = 0
				for s in range(len(sentences)):
					sentence = sentences[s]
					if s not in chain_sentence_indices:
						# add a ... if i'm skipping something and the ... is not already there
						if cloze_div[-1] != '...':
							cloze_div.append('...')
					for t in range(len(sentence['tokens'])):
						token = sentence['tokens'][t]
						wordform = token['originalText']
						if s in chain_sentence_indices:
							if t in chain_event_starts[s]:
								chain_reference_doc.append('<b><font color="steelblue">')
								cloze_div.append('<span class="cloze document' + file_number + ' chain' + str(chain_index) + ' cloze' + str(cloze_index) + '">')
								cloze_index += 1
							if t in chain_entity_starts[s]:
								chain_reference_doc.append('<b><font color="navy">')
							chain_reference_doc.append(wordform)
							cloze_div.append(wordform)
							if t+1 in chain_entity_ends[s]:
								# might have to close multiple times if different phrases end in the same place
								for k in range(len(filter(lambda x: x==t+1, chain_entity_ends[s]))):
									chain_reference_doc.append('</font></b>')
							if t+1 in chain_event_ends[s]:
								# might have to close multiple times if different phrases end in the same place
								for k in range(len(filter(lambda x: x==t+1, chain_event_ends[s]))):
									chain_reference_doc.append('</font></b>')
									cloze_div.append('</span>')
						else:
							chain_reference_doc.append(wordform)
				cloze_div.append('</p></div>')
				chain_reference_doc.append('</body></html>')

				## write chain reference
				chain_reference_filename = 'documents/dinnersfromhell-document' + file_number + ' chain' + str(chain_index) + '.html'
				w = codecs.open(chain_reference_filename, 'w', encoding='utf-8')
				w.write(cleanup_parsed_and_processed_text(' '.join(chain_reference_doc)))
				w.close()

				chain_divs.append(cleanup_parsed_and_processed_text(' '.join(cloze_div)))
				chain_index +=1

		docstring = '\n'.join(
			[
				'<DOCNAME>' + filename,
				'<UUID>' + str(uuid.uuid4())
			] + map(lambda chain: ' '.join(chain), chains))

		documents.append(docstring)

w = codecs.open('restaurants_train_100docs', 'w', encoding='utf-8')
w.write('\n\n'.join(documents))
w.close()

f = open('master_cloze_html_head.html', 'r')
html_head = f.read()
f.close()

f = open('master_cloze_html_tail.html', 'r')
html_tail = f.read()
f.close()

w = codecs.open('master_cloze.html', 'w', encoding='utf-8')
w.write(html_head + '\n\n' + '\n\n'.join(chain_divs) + '\n\n' + html_tail)
w.close()
