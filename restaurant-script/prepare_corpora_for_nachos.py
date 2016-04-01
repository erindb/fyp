import sys

cloze_document = sys.argv[1]

k=-1

## print cloze tests
fp = open('full_training_set', "r")
w_cloze = open('restaurants_cloze_tests.txt', 'w')
w_train = open('restaurants_train', 'w')
docname = None
wf = w_cloze
#for x in sys.stdin:
for line in fp:
  x = line.strip()
  if x.startswith("#"):
    if i!=int(cloze_document):
      w_train.write(line)
    continue
  if x.startswith("<DOCNAME>"):
    k += 1
    docname = x.split('-')[-1].split('.')[0]
    if k!=int(cloze_document):
      w_train.write(line)
    continue
  if x.startswith("<"):
    if k!=int(cloze_document):
      w_train.write(line)
    continue
  if x == "":
    if k!=int(cloze_document):
      w_train.write(line)
    continue
  if x.isspace():
    if k!=int(cloze_document):
      w_train.write(line)
    continue
  seq = x.split()
  L = len(seq)
  if L == 0:
    if k!=int(cloze_document):
      w_train.write(x)
    continue
  if k==int(cloze_document):
    wf.write("<DOCNAME>" + docname + "\n\n")
    wf.write("<CHAIN> len:"+str(L) + '\n')
    for (w, i) in zip(seq, range(L)):
      wf.write("<TEST>\n")
      #remove answer from chain
      test = seq[0:i]+seq[i+1:]
      wf.write("<ANSWER> "+w+'\n')
      assert w == seq[i]
      wf.write("<INSERT_INDEX> "+str(i)+'\n')
      wf.write("<CLOZE> "+' '.join(test)+'\n')
  else:
    w_train.write(line)

fp.close()
w_cloze.close()
w_train.close()

## gzip the training set
import gzip
import shutil
with open('restaurants_train', 'rb') as f_in, gzip.open('restaurants_train.gz', 'wb') as f_out:
  shutil.copyfileobj(f_in, f_out)

## make filelist pointing there
with open('filelist.txt', 'wb') as w:
  w.write('../../restaurant-script/restaurants_train.gz\n')
  w.close()
