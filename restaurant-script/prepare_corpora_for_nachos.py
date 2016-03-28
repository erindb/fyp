fp = open('restaurants_cloze', "r")
wf = open('restaurants_cloze_tests.txt', 'w')

docname = None

#for x in sys.stdin:
for x in fp:
  x = x.strip()
  if x.startswith("#"):
    continue
  if x.startswith("<DOCNAME>"):
    docname = x.split('-')[-1].split('.')[0]
    continue
  if x.startswith("<"):
    continue
  if x == "":
    continue
  if x.isspace():
    continue
  seq = x.split()
  L = len(seq)
  if L == 0:
    continue
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

fp.close()
wf.close()