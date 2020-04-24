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


    def cos_sim(self,user_query,sent_embeds, top=10):
        retval = []
        query_embed = self.model(user_query)
        for sent_embed in sent_embeds:
            sim = int(float(1 - distance.cosine(query_embed,sent_embed[1]))*10000)/10000
            retval.append((sent_embed[0], sim))
        retval = sorted(retval, key = lambda x:x[1], reverse=True)[:top]
        return retval

    def doc_cos_sim(self, doc_sentid_embeds, model_sentid_embeds,top=10):
        retval = []
        for doc_sentid_embed in doc_sentid_embeds:
            for model_sentid_embed in model_sentid_embeds:
                sim = float(1 - distance.cosine(doc_sentid_embed[1],model_sentid_embed[1]))
                retval.append((doc_sentid_embed[0], model_sentid_embed[0], sim))
        retval = sorted(retval, key = lambda x:(x[0],-1*x[2]))
        new = []
        count = {}
        for tup in retval:
            count[tup[0]] = count.get(tup[0],0) + 1
            if count[tup[0]] <= top:
                new.append(tup)
        return new

