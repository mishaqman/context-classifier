import pickle
import sys
import csv
import spacy

class Chunking:

    def set_nlp(self,tagger=False):
        if self.nlp is None:
            if not tagger:
                self.nlp = spacy.load('en_core_web_sm', disable=['tagger','parser','ner'])
            else:
                self.nlp = spacy.load('en_core_web_sm', disable=['parser','ner'])
            self.nlp.add_pipe(self.nlp.create_pipe('sentencizer'))
            self.nlp.max_length = 40000000

    def unset_nlp(self):
        self.nlp = None

    def __init__(self):

        self.unset_nlp()

        self.prohibited_lemmas = set("""
            more new another else extra farther fresh further spare aforesaid
            akin alike regarding corresponding like said similar such suchlike
            that abounding countless manifold multiplied several umpteen uncounted
            varied various many many-sided unlike very other only less same few
            certain this be have include become do relevant following
            """.split())

        self.tokens_with_no_prefix_space = [',',';','.',"'s",':',')',']','}','%','-','?']
        self.tokens_with_no_suffix_space = ['(','[','{','-','$']

        self.sent_char_length = 300

        self.rules = [
            
            {
                'chunk'  : 'e',
                'start'  : set(['NNP','NNPS','CD']),
                'middle' : set(['NNP','NNPS','IN','HYPH','CC','CD']),
                'end'    : set(['NNP','NNPS','CD']),
                'must_have' : set(['NNP','NNPS'])
            },

            
            {
                'chunk'  : 'x',
                'start'  : set(['$','CD']),
                'middle' : set(['$','CD','HYPH']),
                'end'    : set(['CD','NN','NNS'])
            },

            {
                'chunk'  : 'n',
                'previous_prohibited': set(['VB','VBD','VBP','VBZ','RB','RBR','RBS']),
                'start'  : set(['NN','NNS','JJ','JJR','JJS','VBN','VBG','NNP','NNPS']),
                'middle' : set(['NN','NNS','JJ','JJR','JJS','VBN','VBG','HYPH']),
                'end'    : set(['NN','NNS'])
            },

            # {
            #     'chunk'  : 'v',
            #     'start'  : set(['VB','VBD','VBP','VBZ','VBG','VBN']),
            #     'middle' : set(['VB','VBD','VBP','VBZ','VBG','VBN']),
            #     'end'    : set(['VB','VBD','VBP','VBZ','VBG','VBN'])
            # },

            # {
            #     'chunk'  : 'j',
            #     'start'  : set(['JJ','JJR','JJS']),
            #     'middle' : set(['JJ','JJR','JJS']),
            #     'end'    : set(['JJ','JJR','JJS'])
            # },

            # {
            #     'chunk'  : 'r',
            #     'start'  : set(['RB','RBR','RBS']),
            #     'middle' : set(['RB','RBR','RBS']),
            #     'end'    : set(['RB','RBR','RBS'])
            # }

        ]

    def normalize_text(self,text):
        for punct in self.tokens_with_no_prefix_space:
            text = text.replace(' {}'.format(punct),punct)
        for punct in self.tokens_with_no_suffix_space:
            text = text.replace('{} '.format(punct),punct)
        return text

    def text_to_pos(self,text):
        """
        Compute POS tags per sentence from spacy
        """
        self.set_nlp(tagger=True)
        doc = self.nlp(text)
        sentence_pos = []
        sentence_text = []
        for sent in doc.sents:
            sent_pos = []
            for t in sent:
                if t.tag_ == '':
                    continue
                if t.tag_ in ['VBG','VBN']:
                    sent_pos.append((t.text,t.text.lower(),t.tag_))
                else:
                    sent_pos.append((t.text,t.lemma_,t.tag_))
            if len(sent_pos) == 0:
                continue
            sentence_pos.append(sent_pos)
            sentence_text.append(sent.text)
        return sentence_pos, sentence_text

    def text_to_docchunk(self,text):
        sentence_pos, sentence_text = self.text_to_pos(text)
        docchunk = [self.sentpos_to_sentchunk(sent) for sent in sentence_pos]
        return docchunk, sentence_text

    def sentpos_to_sentchunk(self,sent_pos):
        """
        Append a column to POS tags in IOB format to identify chunks
        """
        parse = [[w[0],w[1],w[2],set()] for w in sent_pos]
        if len(parse) == 0:
            return []
        if parse[-1][0] not in ['.','?','!']:
            parse.append(['.','.','.',set()])
            
        for p in range(len(parse)):
            if p == 0:
                parse[0][3] = set([r for r in range(len(self.rules)) if parse[0][2] in self.rules[r]['start']])
                continue
            for r in range(len(self.rules)):
                if (parse[p][2] in ['NNP','NNPS'] or parse[p][1] not in self.prohibited_lemmas) and \
                   ((r not in parse[p-1][3] and parse[p][2] in self.rules[r]['start'] and \
                         parse[p-1][2] not in self.rules[r].get('previous_prohibited',set())) or \
                    (r in parse[p-1][3] and parse[p][2] in (self.rules[r]['middle'] | self.rules[r]['end']))) and \
                   (self.rules[r]['chunk'] != 'e' or parse[p][2] != 'IN' or parse[p][1] in ['of','on']) and \
                   (self.rules[r]['chunk'] != 'e' or parse[p][2] != 'CC' or parse[p][1] == '&'):
                    parse[p][3].add(r)
                else:
                    i = p-1
                    while i >= 0 and r in parse[i][3] and parse[i][2] not in self.rules[r]['end']:
                        parse[i][3].remove(r)
                        i -= 1
                    if self.rules[r]['chunk'] == 'e':
                        must_have = set()
                        new_i = i
                        while new_i >= 0 and r in parse[new_i][3]:
                            must_have.add(parse[new_i][2])
                            new_i -= 1
                        if len(must_have & self.rules[r]['must_have']) == 0:
                            while i >= 0 and r in parse[i][3]:
                                parse[i][3].remove(r)
                                i -= 1

        return [(w[0],w[1],w[2],self.rules[min(w[3])]['chunk'] if len(w[3])>0 else 'o') for w in parse]

    def docchunk_to_chunkmap(self,doc_chunks):
        chunkmap = {}
        sentid = -1
        for sent in doc_chunks:
            sentid += 1
            chunks = set()
            chunk = []
            chunk_type = 'o'
            for word in sent:
                if word[3] == chunk_type:
                    chunk.append(word)
                else:
                    if len(chunk) > 0 and chunk_type != 'o':
                        chunk_text = self.normalize_text(' '.join([(c[0] if (chunk_type == 'e' or chunk_type == 'x') else c[1]) for c in chunk]))
                        chunks.add((chunk_type,chunk_text))
                    chunk = [word]
                    chunk_type = word[3]
            if len(chunk) > 0 and chunk_type != 'o':
                chunk_text = self.normalize_text(' '.join([(c[0] if chunk_type == 'e' else c[1]) for c in chunk]))
                chunks.add((chunk_type,chunk_text))
            for c in chunks:
                if c not in chunkmap:
                    chunkmap[c] = set()
                chunkmap[c].add(sentid)
        return chunkmap


    def sent_terms(self,text):

        sentence_pos, sentence_text = self.text_to_pos(text)
        docchunk = [self.sentpos_to_sentchunk(sent) for sent in sentence_pos]
        sent_terms = self.docchunk_to_chunkmap(docchunk)


        return list(sent_terms.keys())




if __name__ == '__main__':

    infile = sys.argv[1]
    outfile = sys.argv[2]

    text = open(infile,'rb').read()
    text = text.decode('utf-8', 'ignore')

    C = Chunking()
    sentence_pos, sentence_text = C.text_to_pos(text)
    docchunk = [C.sentpos_to_sentchunk(sent) for sent in sentence_pos]
    chunkmap = C.docchunk_to_chunkmap(docchunk)

    retval = {'sentence_pos': sentence_pos,
              'chunkmap': chunkmap}

    pickle.dump(retval, open(outfile,'wb'))

    for sent in retval['sentence_pos']:
        for token in sent:
            print(token)
        print()

    for chunk in chunkmap:
        print([chunk,chunkmap[chunk]])


