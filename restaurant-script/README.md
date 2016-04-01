# pipeline

1. extract links (reads dinners-from-hell-archive-index.html, writes dinnersfromhell-links.csv)
2. read corpus (reads dinnersfromhell-links.csv and dinnersfromhell.com, writes documents/*)
3. transfer to server with corenlp, better ram, etc. to parse
	* `wget --post-file ~/fyp/documents/dinnersfromhell-document-000.txt 'localhost:9000/?properties={"tokenize.whitespace": "true", "annotators": "tokenize,ssplit,pos,coref", "outputFormat": "json"}' -O -`
	* depends on java 8
	* requires 4g ram
	* the server version times out for documents of this length
	* takes in `documents/dinnersfromhell-document-*.txt` files and outputs `documents/*.json` files
4. cavemanify (reads `documents/*.json` files, writes `restaurants_train`)
5. `prepare_corpora_for_nachos.py`
	* extract one document from `restaurants_train` to generate cloze tests
	* gzip restaurants_train
	* depends on `model.py` and `utils.py` from `https://github.com/rudinger/nachos`
6. run nachos and cache model (reads `restaurants_train.gz` and the corresponding cloze tests, writes `restaurant_model.dill`)
	* `python nachos.py -docmin 3 -threshold 10 -so -coref all -cloze_file ../restaurant_data/cloze_tests/restaurant_cloze_20docs -file_list ../restaurant_data/restaurant_file_list`
7. visualize_script makes a graph of the events

# notes

* rudinger et al excluded 94 off-topic stories "(e.g., letters to the webmaster, dinners
not at restaurants)"
* rudinger manually coded "relevant to restaurants" for the cloze tests

# to-do

* all the documents
* select a few good cloze tasks
* start making JS with those cloze tasks
* email rudinger et al for full cloze list (& params?)
* check that we get similar results


python nachos.py -docmin 5 -threshold 1 -coref all -cloze_file ../../restaurant-script/restaurants_cloze_tests.txt -file_list ../../restaurant-script/filelist.txt -model_out ../../restaurant-script/model.dill -model bigram