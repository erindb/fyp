import json
import codecs
import random

with codecs.open('all_chains_data.json', 'rb', 'utf-8') as f:
	jsonStr = f.read()

data = json.loads(jsonStr)

experiment3_data = []

documents = set([d['docIndex'] for d in data])
for doc in documents:
	document_data = [d for d in data if d['docIndex']==doc]
	chains = [d for d in document_data if d['ncloze']>1]
	chainIDs = set([d['chainID'] for d in chains])
	clozeTests = []
	if len(chainIDs) == 1:
		## if # chains == 1, try to get 3 cloze tasks
		## from that chain if we can
		ncloze = chains[0]['ncloze']
		if ncloze > 3:
			clozeIndices = random.sample(range(ncloze), 3)
		else:
			clozeIndices = range(ncloze)
		for clozeIndex in clozeIndices:
			clozeTests.append({
				'clozeIndex': clozeIndex,
				'chainID': list(chainIDs)[0]
			})
	elif len(chainIDs) > 1:
		## if # chains > 1, try to get 3 cloze tasks:
		## 2 from one chain and 1 from another.
		twoChains = random.sample(chainIDs, 2)
		firstChain = True
		for chainID in twoChains:
			chain_data = [d for d in chains if d['chainID']==chainID]
			if firstChain:
				clozeIndices = random.sample(range(len(chain_data)), 2)
			else:
				clozeIndices = random.sample(range(len(chain_data)), 1)
			for clozeIndex in clozeIndices:
				clozeTests.append({
					'clozeIndex': clozeIndex,
					'chainID': chainID
				})
			firstChain = False

	if len(clozeTests) > 0:
		experiment3_data.append({
			'docIndex': doc,
			'clozeTests': clozeTests
		})

with codecs.open('experiment3_data.json', 'wb', 'utf-8') as w:
	w.write(json.dumps(experiment3_data))