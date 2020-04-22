import nltk
import os
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
from itertools import islice
from scipy.spatial import distance


class DocManager:

    def __init__(self,use_model):

        self.model = hub.load(use_model)

    def doc_to_sent(self,document_text):

        sentences = []
        text = document_text.strip()
        paras = text.split('\n\n')
        paracount = -1
        for para in paras:
            paracount += 1
            sentcount = -1
            sents = nltk.tokenize.sent_tokenize(para)
            for sent in sents:
                sentcount +=1
                sentences.append((paracount, sentcount, sent))
        return sentences


    def sent_to_embeddings(self, sent_list, batch_size=40000):

        all_embeddings = []
        batches = 1 + (len(sent_list)//batch_size)
        sentences = iter(sent_list)
        split_sentences = [list(islice(sentences, batch_size)) for _ in range(batches)]
        for sents in split_sentences:
            all_embeddings.extend(self.model(sents))
        all_embeddings = np.array(all_embeddings)

        return all_embeddings


    def cos_sim(self,user_query,sent_embeds):
        cos_sim = []
        query_embed = self.model(user_query)
        for sent_embed in sent_embeds:
            sim = int(float(1 - distance.cosine(query_embed,sent_embed[1]))*10000)/10000
            cos_sim.append((sent_embed[0], sim))
        cos_sim = sorted(cos_sim, key = lambda x:x[1], reverse=True)[:25]
        return cos_sim




