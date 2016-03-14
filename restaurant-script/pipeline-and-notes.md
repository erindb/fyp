# pipeline

1. extract links (reads dinners-from-hell-archive-index.html, writes dinnersfromhell-links.csv)
2. read corpus (reads dinnersfromhell-links.csv and dinnersfromhell.com, writes documents/*)
3. transfer to server with corenlp, better ram, etc. to parse
	* `wget --post-file ~/fyp/documents/dinnersfromhell-document-000.txt 'localhost:9000/?properties={"tokenize.whitespace": "true", "annotators": "tokenize,ssplit,pos,coref", "outputFormat": "json"}' -O -`
	* depends on java 8
	* requires 4g ram
	* the server version times out for documents of this length
	* takes in `documents/dinnersfromhell-document-*.txt` files and outputs `documents/*.json` files
4. cavemanify (reads `documents/*.json` files
	* writes `restaurants_train`
	* writes `restaurants_cloze`
	* writes `master_cloze.html`, which is the html file for `experiment 1`
5. process cloze tests: reads `restaurants_cloze`, writes `restaurants_cloze_tests.txt`
6. run model on `restaurants_train`, evaluating on `restaurants_cloze_tests.txt`, writes `restaurants.dill`, which stores aysmmetric bigram probabilities for all event pairs

<!--
5. extract one document from `restaurants_train` to generate cloze tests using nachos scripts
	* `model.py` and `utils.py` come from `https://github.com/rudinger/nachos`
6. run nachos and cache model (reads `restaurants_train` and the corresponding cloze tests, writes `restaurant_model.dill`)
7. visualize_script makes a graph of the events
-->

# notes

* rudinger et al excluded 94 off-topic stories "(e.g., letters to the webmaster, dinners
not at restaurants)"
* rudinger manually coded "relevant to restaurants" for the cloze tests

# to-do

* email rudinger et al for full cloze list (& params?)
* check that we get similar results