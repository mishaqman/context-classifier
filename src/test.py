# import chunking
import csv
import glob

# C = chunking.Chunking()
# out = csv.writer(open('chunks.csv', 'w', newline = ''))
# for f in glob.iglob('../../../../Downloads/kintext/*.txt'):
# 	text = open(f, 'r', errors = 'ignore').read()
# 	sentence_pos, sentence_text = C.text_to_pos(text)
# 	docchunk = [C.sentpos_to_sentchunk(sent) for sent in sentence_pos]
# 	chunkmap = C.docchunk_to_chunkmap(docchunk)
# 	for k,v in chunkmap.items():
# 		if len(k[1]) > 2:
# 			out.writerow([f.split('/')[-1],k[1],k[0],len(v)])

hey = ['associated', 'associates', 'association', 'bank', 'chartered', 'chtd', 'chtd.', 'church', 'club', 'co', 'co-op', 'co.', 'college', 'committee', 'company', 'cooperative', 'corp', 'corp.', 'corporation', 'credit union', 'd p c', 'd.p.c.', 'deposit', 'design professional corporation', 'dpc', 'foundation', 'fund', 'guild', 'inc', 'inc.', 'incorporated', 'institute', 'l 3 c', 'l c', 'l l c', 'l.3.c.', 'l.c.', 'l.l.c.', 'l3c', 'lc', 'lc.', 'league', 'limited', 'limited company', 'limited liability', 'limited liability co', 'limited liability co.', 'limited liability company', 'llc', 'llc.', 'low-profit limited liability company', 'ltd', 'ltd liability co', 'ltd liability company', 'ltd.', 'ltd. liability co.', 'ltd. liability company', 'medical', 'nfp', 'p a', 'p c', 'p l l c', 'p l p', 'p s', 'p s c', 'p. c.', 'p.a', 'p.a.', 'p.c', 'p.c.', 'p.l.l.c.', 'p.l.p.', 'p.s.', 'p.s.c.', 'pa', 'pc', 'plc', 'plc.', 'pllc', 'plp', 'prof corp', 'prof. corp.', 'professional', 'professional association', 'professional association, p a', 'professional association, p.a.', 'professional association, pa', 'professional company', 'professional corporation', 'professional limited company', 'professional limited liability company', 'professional service', 'professional service corporation', 'professional services', 'ps', 'psc', 's c', 's p c', 's.c.', 's.p.c.', 'sc', 'service corporation', 'services', 'social purpose corporation', 'society', 'spc', 'syndicate', 'trust', 'trust company', 'union', 'university']

for i in hey:
	print(i)




