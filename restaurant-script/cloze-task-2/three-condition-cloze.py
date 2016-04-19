import json
import re
import copy
import codecs
import random

writeInnerHtml = codecs.open('../../experiment3/innerHTML.html', 'w', 'utf-8')

clozeData = []

for docIndex in [
	'022', '023', '025', '033', '037',
	'050', '063', '086', '120', '141',
	'151', '153', '162', '171', '177',
	'191', '196', '243', '248', '271'
]:
# for docIndex in ['022']:
	clozeData.append({
		"document": docIndex
		})
	clozeDataElem = clozeData[-1]
	# print "document",
	# print docIndex

	with open('../documents/dinnersfromhell-document-' + docIndex +'.txt.json', 'r') as f:
		jsonFile = f.read()
	with open('../documents/dinnersfromhell-document-' + docIndex +'.txt', 'r') as f:
		txtFile = f.read()

	def cleanStr(string):
		string = re.sub(' ([.,!?\'])', '\g<1>', string)
		string = re.sub('(`) ', '\g<1>', string)
		string = re.sub('``', '"', string)
		string = re.sub('-(LRB|RRB)-', '--', string)
		return re.sub(' n\'t', 'n\'t', string)
	def fixIndex(i):
		return i-1
	def breakIndex(i):
		return i+1
	def getCavemanArgs(sentence):
		dependencies = sentence['collapsed-dependencies']
		headDep = filter(lambda x: x['dep']=='ROOT', dependencies)[0]
		headIndex = fixIndex(headDep['dependent'])
		headArguments = filter(lambda x: x['governor'] == breakIndex(headIndex), dependencies)
		headArgumentIndices = map(lambda x: x['dependent'], headArguments)
		conjArguments = filter(lambda x: x['dep']=='conj:and' and x['governor'] in headArgumentIndices, dependencies)
		cavemanArguments = filter(isCaveman, headArguments)
		return cavemanArguments + conjArguments
	def getWord(w):
		return w['word']
	def getLemma(w):
		return w['lemma']

	def indexInMentions(argIndex, sentIndex, mentions):
		# print len(mentions)
		# print sentIndex
		# print 
		for mention in mentions:
			if sentIndex == fixIndex(mention['sentNum']):
				startIndex = fixIndex(mention['startIndex'])
				endIndex = fixIndex(mention['endIndex'])
				# print startIndex,
				# print argIndex,
				# print endIndex
				return startIndex <= argIndex and argIndex <= endIndex
		return False

	def spanify(sent, clozeIndex, docIndex, chainIndex, sentType, sentence):
		return "<p class='blurry " + sentType + " cloze document" + \
			docIndex + " cloze" + str(clozeIndex) + " chain" + \
			str(chainIndex) + "'>" +  full_sentence_from_sentence_object(sentence) + "</p>" +  \
			"<p class='gloss " + sentType + " cloze document" + \
			docIndex + " cloze" + str(clozeIndex) + " chain" + \
			str(chainIndex) + "'>" +  sent + "</p>"

	def mentionInDep(mention, dep, sentence):
		## first, check if sentence has ccomp
		startIndex = fixIndex(mention['startIndex'])
		endIndex = fixIndex(mention['endIndex'])
		headIndex = fixIndex(dep['dependent'])
		#return false if argument is out of bounds of mention
		if headIndex < startIndex: return False
		if headIndex > endIndex: return False
		if startIndex + 1 == endIndex: return True
		#return false if mention is not head of argument
		# print sentence['tokens'][headIndex]['lemma']
		# print mention['text']
		# print map(getWord, sentence['tokens'][startIndex:endIndex])
		# print mention[startIndex:endIndex]
		return True

	def modifyDep(dep, argIndex, govIndex):
		if dep['dependent'] == argIndex:
			dep['dep'] = 'ROOT'
		elif dep['dependent'] == govIndex:
			dep['dep'] = 'OLD_ROOT'
		return dep

	def mentionIsInCaveman(mention, sentence):
		# given a mention and the sentence it occurs in,
		# determine whether the mention is a main argument
		# to the head verb
		cavemanArgs = getCavemanArgs(sentence)
		cavemanMentions = filter(lambda dep: mentionInDep(mention, dep, sentence), cavemanArgs)
		return len(cavemanMentions) > 0

	def isCaveman(dep):
		typeOfDep = dep['dep']
		m = re.match('(nsubj|dobj|neg|nsubjpass|ccomp|nmod.*)', typeOfDep)
		if m:
			return True
		return False

	def isPrep(typeOfDep):
		m = re.match('nmod.*', typeOfDep)
		if m:
			return True
		return False

	def full_sentence_from_sentence_object(sentence):
		tokens = map(lambda x: x['word'], sentence['tokens'])
		return cleanStr(' '.join(tokens));

	def cavemanify(sentence, lookForAnd=True, lookForComp=True, VSify=False, mentionKey=None):
		dependencies = sentence['collapsed-dependencies']
		headDep = filter(lambda x: x['dep']=='ROOT', dependencies)[0]
		headWord = sentence['tokens'][fixIndex(headDep['dependent'])]
		cavemanArguments = getCavemanArgs(sentence)
		tokens = sentence['tokens']
		cavemanSentence = []
		VSSentence = []
		# print headWord
		isPassive = headWord['pos'] == 'VBN'
		argTypes = map(lambda x: x['dep'], cavemanArguments)
		if 'nsubjpass' in argTypes:
			arg = cavemanArguments[argTypes.index('nsubjpass')]
			argIndex = fixIndex(arg['dependent'])
			cavemanSentence.append(tokens[argIndex]['lemma'])
			# #### check if nsubjpass is mention
			if VSify:
				mentionIndices = corefs[mentionKey]
				if indexInMentions(argIndex, sentIndex, mentionIndices):
					VSSentence.append(tokens[argIndex]['lemma'])
		if 'nsubj' in argTypes:
			arg = cavemanArguments[argTypes.index('nsubj')]
			argIndex = fixIndex(arg['dependent'])
			cavemanSentence.append(tokens[argIndex]['lemma'])
			if VSify:
				mentionIndices = corefs[mentionKey]
				# print map(lambda x: x['text'], mentionIndices)
				if indexInMentions(argIndex, sentIndex, mentionIndices):
					VSSentence.append(tokens[argIndex]['lemma'])
					# print VSSentence
		if 'neg' in argTypes:
			cavemanSentence.append('not')
		if isPassive:
			cavemanSentence.append(headWord['word'])
			VSSentence.append(headWord['word'])
		else:
			cavemanSentence.append(headWord['lemma'])
			VSSentence.append(headWord['lemma'])
			# print VSSentence
		if 'dobj' in argTypes:
			arg = cavemanArguments[argTypes.index('dobj')]
			argIndex = fixIndex(arg['dependent'])
			cavemanSentence.append(tokens[argIndex]['lemma'])
			if VSify:
				theseMentions = corefs[mentionKey]
				# print theseMentions
				# print argIndex
				if indexInMentions(argIndex, sentIndex, theseMentions):
					VSSentence.append(tokens[argIndex]['lemma'])
		isCompositeSubj = False
		isCompositeVerb = False
		if 'conj:and' in argTypes:
			arg = cavemanArguments[argTypes.index('conj:and')]
			argIndex = fixIndex(arg['dependent'])
			govIndex = fixIndex(arg['governor'])
			govDep = filter(lambda x: x['dependent']==breakIndex(govIndex), dependencies)[0]

			imaginarySentence = copy.deepcopy(sentence)
			if govDep['dep']=='nsubj' and lookForAnd:
				isCompositeSubj = True
				## repeat sentence with conj:and word filled in where its governor was
				imaginarySentence['tokens'][govIndex] = imaginarySentence['tokens'][argIndex]
				imaginarySentence['tokens'][govIndex]['index'] = govIndex
				additionalCavemanSentence = cavemanify(imaginarySentence, False, lookForComp)
			if govDep['dep']=='ROOT' and lookForComp:
				isCompositeVerb = True
				## repeat sentence with ROOT pointing to the new ccomp
				imaginarySentence['dependencies'] = map(lambda dep: modifyDep(dep, argIndex, govIndex), dependencies)
				additionalCCompCavemanSentence = cavemanify(imaginarySentence, lookForAnd, False)
		preps = filter(isPrep, argTypes)
		for prep in preps:
			m = re.match('nmod:?(.*)', prep)
			prepositionText = m.groups(1)[0]
			if prepositionText not in ['tmod', 'npmod']:
				if prepositionText == 'agent':
					prepositionText = 'by'
				cavemanSentence.append(prepositionText)
				arg = cavemanArguments[argTypes.index(prep)]
				argIndex = fixIndex(arg['dependent'])
				cavemanSentence.append(tokens[argIndex]['lemma'])
		cavemanSentencesToReturn = [' '.join(cavemanSentence)]
		if isCompositeSubj:
			cavemanSentencesToReturn.append(additionalCavemanSentence)
		if isCompositeVerb:
			cavemanSentencesToReturn.append(additionalCCompCavemanSentence)
		if VSify:
			return ' '.join(VSSentence).capitalize() + '.'
		else:
			return ' '.join(cavemanSentencesToReturn).capitalize() + '.'

	nlpJSON = json.loads(jsonFile)
	sentences = nlpJSON['sentences']
	corefs = nlpJSON['corefs']
	refIDs = corefs.keys()
	chains = []
	chainIndex = -1

	for key in refIDs:
		# print key
		coref = corefs[key]

		cavemanMentions = filter(lambda mention: mentionIsInCaveman(mention, sentences[fixIndex(mention['sentNum'])]), coref)
		mentionIndices = list(set(map(lambda x: x['sentNum'], cavemanMentions)))

		if len(mentionIndices) > 1:
		# 	bestArgWord = None
		# 	for cavemanMention in cavemanMentions:
		# 		startIndex = cavemanMention['startIndex']
		# 		endIndex = cavemanMention['endIndex']
		# 		## find a cavemanArg that's in this range
		# 		sentIndex = fixIndex(cavemanMention['sentNum'])
		# 		sentence = sentences[sentIndex]
		# 		cavemanArgs = getCavemanArgs(sentence)
		# 		argsInRange = filter(lambda x: startIndex <= x['dependent'] and x['dependent'] <= endIndex, cavemanArgs)
		# 		if cavemanMention['isRepresentativeMention']:
		# 			bestArg = argsInRange[0]
		# 			bestArgIndex = fixIndex(bestArg['dependent'])
		# 			bestArgWord = sentence['tokens'][bestArgIndex]
		# 		elif cavemanMention['type'] == 'PRONOMINAL':
		# 			if bestArgWord:
		# 				for arg in argsInRange:
		# 					argIndex = fixIndex(arg['dependent'])
		# 					token = sentence['tokens'][argIndex]
		# 					## if dependency type isn't nmod:poss
		# 					dependencies = sentence['collapsed-dependencies']
		# 					dep = filter(lambda x: x['dependent']==breakIndex(argIndex), dependencies)[0]
		# 					if dep['dep'] not in ['nmod:poss']:
		# 						sentence['tokens'][argIndex]['lemma'] = bestArgWord['lemma']
		# 				# sentence['tokens']
		# 		# 	representativeStart = cavemanMention['start']
		# 		# if cavemanMention
			chains.append({
				'fullSentences': [],
				'cavemanSentences': [],
				'simpleEvents': []
			})
			chainIndex +=1
			chain = chains[-1]
			lastSentence = -1
			## chain has at least 2 links
			# print len(mentionIndices)
			clozeTestIndex = -1
			for mention in cavemanMentions:
				sentIndex = fixIndex(mention['sentNum'])
				sentence = sentences[sentIndex]

				chain['fullSentences'].append("<div class='story_segment sentence'>")
				chain['cavemanSentences'].append("<div class='story_segment sentence'>")
				chain['simpleEvents'].append("<div class='story_segment sentence'>")

				## get full sentences in chain
				fullSentence = cleanStr(' '.join(map(lambda x: x['word'], sentence['tokens'])))
				previousSpanifiedSentence = spanify(fullSentence, clozeTestIndex, docIndex, chainIndex, 'full', sentence)
				# if fullSentence == "We crossed that pub off our list.":
				# 	print previousSpanifiedSentence
				if previousSpanifiedSentence not in chain['fullSentences']:
					clozeTestIndex += 1
					spanifiedSentence = spanify(fullSentence, clozeTestIndex, docIndex, chainIndex, 'full', sentence)
					chain['fullSentences'].append(spanifiedSentence)
					chain['cavemanSentences'].append(spanify(cavemanify(sentence), clozeTestIndex, docIndex, chainIndex, 'caveman', sentence))
					# print key
					chain['simpleEvents'].append(spanify(
						cavemanify(sentence, VSify=True, mentionKey=key), clozeTestIndex, docIndex, chainIndex, 'event', sentence))
					## get caveman in chain
					## get VS in chain
				# else:
				# 	print 'repeat'

				chain['fullSentences'].append("</div>")
				chain['cavemanSentences'].append("</div>")
				chain['simpleEvents'].append("</div>")

	if len(chains) == 1:
		## sample 3 cloze tasks from same chain
		chainsToTest = [0]
		nEvents = len(chains[0])
		if nEvents < 3:
			clozeTests = range(nEvents)
		else:
			clozeTests = random.sample(range(len(chains[0])), nEvents)
		clozeTests = map(lambda x: (chainsToTest[0], x), clozeTests)
	else:
		## sample 2 cloze tasks from same chain
		## first sample the longest chain
		lens = map(lambda x: len(x['simpleEvents']), chains)
		# print lens
		maxChainIndex = lens.index(max(lens))
		remainingIndices = range(len(chains))
		remainingIndices.remove(maxChainIndex)
		otherChainIndex = random.sample(remainingIndices, 1)[0]
		# print maxChainIndex,
		# print otherChainIndex
		chainsToTest = [maxChainIndex, otherChainIndex]
		chainIndex = chainsToTest[0]
		nEvents = len(chains[chainIndex])
		clozeTests = map(lambda x: (maxChainIndex, x), random.sample(range(nEvents), 2))
		chainIndex = chainsToTest[1]
		nEvents = len(chains[chainIndex])
		clozeTests += map(lambda x: (otherChainIndex, x), random.sample(range(nEvents), 1))
	# print chainsToTest
	clozeDataElem["clozeTests"] = clozeTests
	chainIndex = -1
	for chain in chains:
		# print chainIndex
		# print chain
		chainIndex += 1
		if chainIndex in chainsToTest:
			threeVersionsOfStory = '\n'.join([
				"<div class='story chain full document" + docIndex + " chain" + str(chainIndex) + "'>",
				' '.join(chain['fullSentences']),
				"</div>",
				"<div class='story chain caveman document" + docIndex + " chain" + str(chainIndex) + "'>",
				' '.join(chain['cavemanSentences']),
				"</div>",
				"<div class='story chain event document" + docIndex + " chain" + str(chainIndex) + "'>",
				' '.join(chain['simpleEvents']),
				"</div>"])
			writeInnerHtml.write(threeVersionsOfStory)

writeInnerHtml.close()
print json.dumps(clozeData)

		# else:
		# 	print docIndex
		# 	print map(lambda mention: mention['text'], coref)
		# for mention in coref:
		# 	sentIndex = fixIndex(mention['sentNum'])
		# 	mentionIsInCaveman(mention, sentences[sentIndex])
	# 		# [ u'sentNum', u'gender', u'position', u'type', u'id']
	# 		isAnimate = mention['animacy'] == 'ANIMATE'
	# 		isRepresentative = mention['isRepresentativeMention']
	# 		mentionText = mention['text']
	# 		number = mention['number']
	# 		endIndex = fixIndex(mention['endIndex'])
	# 		startIndex = fixIndex(mention['startIndex'])
	# 		sentIndex = fixIndex(mention['sentNum'])
	# 		# print mention['gender']
	# 		# print mention['position']
	# 		# print mention['type']
	# 		isLong = startIndex + 1 < endIndex
	# 		# print mentionText
	# 		sentence = sentences[sentIndex]
	# 		tokens = sentence['tokens']
	# 		wordTokens = map(lambda x: x['word'], tokens)
	# 		mentionTokens = tokens[startIndex:endIndex]
	# 		dependencies = sentence['basic-dependencies']

	# 		headWord = filter(lambda x: x['dep']=='ROOT', dependencies)[0]
	# 		headIndex = fixIndex(headWord['dependent'])
	# 		headLemma = tokens[headIndex]['lemma']
	# 		headArguments = filter(lambda x: x['governor'] == breakIndex(headIndex), dependencies)
	# 		cavemanArguments = filter(isCaveman, headArguments)
	# 		mentionDeps =  filter(lambda x: x['dependent']>=startIndex and x['dependent']<=endIndex, cavemanArguments)

	# 		fullSentence = cleanStr(' '.join(wordTokens), False)
	# 		if fullSentences not in fullSentences:
	# 			fullSentences.append(fullSentence)
	# 			cavemans.append(cavemanify(tokens[headIndex], cavemanArguments, tokens))
	# 			VSs.append(VSify(tokens[headIndex], cavemanArguments, tokens))


	# 	# for sentence in fullSentences:
	# 	# 	print sentence,

	# 	# print
	# 	# print

	# 	# for caveman in cavemans:
	# 	# 	print caveman + '.',

	# 	# print
	# 	# print

	# 	# for VS in VSs:
	# 	# 	print VS + '.',

	# 	# print
	# 	# print


	# ### coref chain!!!

	# VSs = []
	# cavemans = []
	# fullSentences = []

	# for s in range(len(sentences)):
	# 	sentence = sentences[s]
	# 	isLast = (s == len(sentences)-1)
	# 	# [u'tokens', u'index', u'basic-dependencies', u'parse', u'collapsed-dependencies', u'collapsed-ccprocessed-dependencies']
	# 	tokens = sentence['tokens']
	# 	wordTokens = map(lambda x: x['word'], tokens)
	# 	fullSentence = cleanStr(' '.join(wordTokens), isLast)
	# 	if isLast and fullSentence.startswith('Sign'):
	# 		continue
	# 	dependencies = sentence['basic-dependencies']
	# 	headWord = filter(lambda x: x['dep']=='ROOT', dependencies)[0]
	# 	headIndex = fixIndex(headWord['dependent'])
	# 	headLemma = tokens[headIndex]['lemma']
	# 	headArguments = filter(lambda x: x['governor'] == breakIndex(headIndex), dependencies)
	# 	cavemanArguments = filter(isCaveman, headArguments)
	# 	fullSentences.append(fullSentence)
	# 	cavemans.append(cavemanify(tokens[headIndex], cavemanArguments, tokens))
	# 	VSs.append(VSify(tokens[headIndex], cavemanArguments, tokens))

	# # for sentence in fullSentences:
	# # 	print sentence,

	# # print
	# # print

	# # for caveman in cavemans:
	# # 	print caveman + '.',

	# # print
	# # print

	# # for VS in VSs:
	# # 	print VS + '.',