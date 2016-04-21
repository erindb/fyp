import codecs
import json

with codecs.open('before.html', 'rb', 'utf-8') as f:
	before = f.read()
with codecs.open('after.html', 'rb', 'utf-8') as f:
	after = f.read()

with codecs.open('all_chains_data.json', 'rb', 'utf-8') as f:
	all_chains_data = json.loads(f.read())

## we only need to load the chains we sampled
## into the html file for the experiment
with codecs.open('experiment3_data.json', 'rb', 'utf-8') as f:
	experiment3_data = json.loads(f.read())

def combine_html(lst_of_lsts):
	return [''.join(some_html) for some_html in lst_of_lsts]

inner_html = []

for document in experiment3_data:
	docIndex = document['docIndex']
	chainIDs = set([d['chainID'] for d in document['clozeTests']])
	for chainID in chainIDs:
		## add chain to innter_html,
		## including all three versions
		## and a response input
		for version in ['caveman', 'event_only', 'original']:
			inner_html +=  combine_html([
				['<div class="story ', version, '">']
			])
			for sentence in [d for d in all_chains_data if d['chainID']==chainID]:
				original_text = sentence['original']
				inner_html += combine_html([
					['<div class="story_segment sentence">'],
					['<p class="blurry">', original_text, '</p>'],
					['<p class="gloss">', sentence[version], '</p>'],
					['</div>']
				])
			inner_html += ['</div>']

print '\n'.join(inner_html)

with codecs.open('../index.html', 'wb', 'utf-8') as w:
	w.write(before + '\n'.join(inner_html) + after)

## EXAMPLE:

# <div class='story'>
# 	<div class='story_segment sentence'>
# 		<p class='blurry'>About 10 minutes later the waitress comes over and says "Good, someone brung yall, yall's drinks''.</p>
# 		<p class='gloss'>About 10 minutes later the waitress comes over and says "Good, someone brung yall, yall's drinks''.</p>
# 	</div>
# 	<div class='story_segment sentence'>
# 		<p class='blurry'>At this point, we ask if we could have some refills and if she knew when our food would be ready.</p>
# 		<p class='gloss'>At this point, we ask if we could have some refills and if she knew when our food would be ready.</p>
# 	</div>
# 	<p class='story_segment prompt'>Please guess the sentence that was here:</p>
# 	<input class='story_segment response'></input>
# 	<div class='story_segment sentence'>
# 		<p class='blurry'>She responds by saying that she has yet to turn in our order to the cook but she was on her way to do it.</p>
# 		<p class='gloss'>She responds by saying that she has yet to turn in our order to the cook but she was on her way to do it.</p>
# 	</div>
# </div>