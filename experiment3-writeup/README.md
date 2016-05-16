I did a lot of little nlp steps on the responses that people gave. It's a mess:

1. experiment3.csv
	- an anonymized, slightly pared down collection of participant's responses
	- how was this made?

2. experiment3-annotated.csv
	- my manual glosses of participants' main verbs and whether they approximately match the original
	- hand modified from experiment3.csv

3. experiment3-with-main-verbs.csv
	- created with dependency-parse-data.py

4. dependency-parse-data.py
	- takes hand modified experiment3-annotated.csv and adds automatic version of gloss based on root.verb and synsets
	- calls local corenlp java file to parse responses, writes tmp-sentences-file.txt and reads tmp-sentences-file.json
	- ultimately writes experiment3-with-main-verbs.csv, which is used in experiment3.Rmd

5. tmp-sentences-file.txt
	- a file for collecting sentences to give to corenlp

6. tmp-sentences-file.json
	- a file that corenlp writes with parses for everything in tmp-sentences-file.txt

7. experiment3.Rmd
	- writeup of results

8. experiment3.pdf
	- compiled writeup of results

9. parse-data.py
	- reads experiment3.csv
	- parses (just pos-tagging) participants' responses using server at erindb.me
	- writes tasks.p

9. tasks.p
	- a file for caching parse data from corenlp server

10. collect-data.py
	- reads tasks.p
	- figures out whether participants' responses contain the main verb of the original
	- writes 