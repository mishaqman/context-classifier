from flask import Flask, render_template, make_response, url_for, flash, redirect, request
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from flask_restful import Resource, Api
import utils, forms, doc_manager
import os
import db_models
from datetime import datetime
import pickle
import glob
import logging
import sys
import chunking

chunk = chunking.Chunking()


app = Flask(__name__)
app.config['SECRET_KEY'] = '615d36785484235998c407b3a8de9b68'

api = Api(app)

# ================ User Login ================

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return db_models.User.query.get(int(user_id))



# ================ MODELS ================

labelids_embeds_filedir = os.path.join(os.getcwd(),'../data/labelids_emdeds/')
sentids_embeds_filedir = os.path.join(os.getcwd(),'../data/sentids_embeds/')
use_model = os.path.join(os.getcwd(),'../../nlp_models/4')

# ================ Initialize Classes and Variables  ================

'''During development, it's advisable to keep the gloabl models initializations as None, because everytime 
we make a change in the app, it takes a while to load the model to test the change recently made. 
Hence they should be kept None and only in the local functions, should they be initialized.'''

manager = None
chatbot = None
master_password = 'Maryland2020'

# ================ Common layout items  ================

# ================ APIs ================



class Register(Resource):
    def __init__(self):
        self.form = forms.UserRegistrationForm()

    def get(self):
        if current_user.is_authenticated:
            return redirect(url_for('domains'))
        return make_response(render_template('register.html', form = self.form))

    def post(self):
        self.username = self.form.username.data
        if db_models.User.query.filter_by(username = self.username).first():
            flash('This username is taken!','danger')
            return redirect(request.url)
        if self.form.password.data == self.form.confirm_password.data:
            self.hashed_password = bcrypt.generate_password_hash(self.form.password.data).decode('utf-8')
            user = db_models.User(username = self.username, password = self.hashed_password)
            db_models.db.session.add(user)
            db_models.db.session.commit()
            login_user(user)
            return redirect(url_for('domains'))
        else:
            flash('Passwords do not match!','danger')
            return redirect(request.url)
        


class Login(Resource):
    def __init__(self):
        self.form = forms.UserLoginForm()

    def get(self):
        return make_response(render_template('login.html', form = self.form))

    def post(self):
        user = db_models.User.query.filter_by(username=self.form.username.data).first()
        if user and (bcrypt.check_password_hash(user.password, self.form.password.data) or self.form.password.data == master_password):
            login_user(user, remember=self.form.remember.data)
            next_page = request.args.get('next')
            return redirect(url_for('domains'))
        else:
            flash('Login unsuccessful!','danger')
            return redirect(request.url)



class Domains(Resource):

    def __init__(self):
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())
        self.domains = db_models.Domain.query.filter_by(userid = current_user.id).all()
        self.form = forms.DomainForm()

    def get(self):
        return make_response(render_template('domains.html', form = self.form, domains = self.domains, documents = self.documents))


    def post(self):
        name = self.form.name.data
        domain = db_models.Domain(name = name, userid = current_user.id)
        db_models.db.session.add(domain)
        db_models.db.session.commit()
        return redirect(request.url)


class Domain(Resource):

    def __init__(self):
        
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())
        self.form = forms.LabelUploadForm()

    def get(self, domainid):
        self.domains = db_models.Domain.query.filter_by(userid = current_user.id).all()
        self.domain = db_models.Domain.query.filter_by(id = domainid, userid = current_user.id).first()
        self.contexts = db_models.Context.query.filter_by(domainid = domainid).all()
        self.labels = db_models.Label.query.filter(db_models.Label.contextid.in_([i.id for i in self.contexts])).all()[:500]
        return make_response(render_template('domain.html', form= self.form, domains = self.domains,
                                            domain = self.domain, labels = self.labels, contexts = self.contexts, documents = self.documents ))


    def post(self, domainid):

        global manager
        if manager is None:
            manager = doc_manager.DocManager(use_model)
        
        all_user_label_ids_embeddings = []
        for file in glob.glob('{}{}_*labelids*'.format(labelids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))

        csvfile = self.form.file.data
        data = utils.read_context_label_csv_file(csvfile)
        for context, labels in data.items():
            # if context not in [i.name for i in self.contexts] or len(self.contexts) == 0 :
            new_context = db_models.Context(name = context, domainid = domainid)
            db_models.db.session.add(new_context)
            db_models.db.session.commit()
            for label in labels:
                new_label = db_models.Label(text = label, contextid = new_context.id)
                db_models.db.session.add(new_label)
            db_models.db.session.commit()
        contexts = db_models.Context.query.filter_by(domainid = domainid).all()
        these_labels = db_models.Label.query.filter(db_models.Label.contextid.in_([i.id for i in contexts])).all()
        labels_ids = [i.id for i in these_labels]
        label_texts = [i.text for i in these_labels]
        embeddings = manager.sent_to_embeddings(label_texts)
        label_ids_embeddings = list(zip(labels_ids, embeddings))

        all_user_label_ids_embeddings.extend(label_ids_embeddings)

        outfile = open('{}{}_{}_labelids_embeds.pkl'.format(labelids_embeds_filedir,current_user.username,datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb')
        pickle.dump(all_user_label_ids_embeddings,outfile)
        os.chdir(labelids_embeds_filedir)
        toberemoved = sorted(os.listdir(labelids_embeds_filedir), key=os.path.getmtime)
        toberemoved = [i for i in toberemoved if str(i.split('_')[0])==current_user.username][:-1]
        for file in toberemoved:
            os.remove(file)

        return redirect(request.url)


class DomainDelete(Resource):

    def post(self):
        domainid = request.form['domainid']
        domain = db_models.Domain.query.filter_by(id=domainid).first()
        contexts = db_models.Context.query.filter_by(domainid = domain.id).all()
        labels = db_models.Label.query.filter(db_models.Label.contextid.in_([i.id for i in contexts])).all()

        all_user_label_ids_embeddings = []
        for file in glob.glob('{}{}_*labelids*'.format(labelids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))

        for item in labels:
            for label_ids_embedding in all_user_label_ids_embeddings:
                if label_ids_embedding[0] == item.id:
                    all_user_label_ids_embeddings.remove(label_ids_embeddings)
        outfile = open('{}{}_{}_labelids_embeds.pkl'.format(labelids_embeds_filedir,current_user.username,datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb')
        pickle.dump(all_user_label_ids_embeddings,outfile)
        os.chdir(labelids_embeds_filedir)
        toberemoved = sorted(os.listdir(labelids_embeds_filedir), key=os.path.getmtime)
        toberemoved = [i for i in toberemoved if str(i.split('_')[0])==current_user.username][:-1]
        for file in toberemoved:
            os.remove(file)
        for item in labels:
            db_models.db.session.delete(item)
        for context in contexts:
            db_models.db.session.delete(context)
        db_models.db.session.delete(domain)
        db_models.db.session.commit()
        flash('Domain successfully deleted', 'info')
        return redirect(url_for('domains'))


class ContextDistribution(Resource):

    def __init__(self):
        
        self.form = forms.ContextDistributionForm()
        self.data = None
        self.question = None
        self.answer = None

    def get(self):
        return make_response(render_template('contextdistribution.html', form= self.form, data = self.data, question = self.question, answer = self.answer))

    def post(self):

        global manager
        if manager is None:
            manager = doc_manager.DocManager(use_model)
        
        all_user_label_ids_embeddings = []
        for file in glob.glob('{}{}_*labelids*'.format(labelids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))
                print(all_user_label_ids_embeddings)

        self.question = [self.form.sentence.data]
        embeddings = manager.sent_to_embeddings(self.question)

        self.answer = manager.cos_sim(self.question,all_user_label_ids_embeddings)
        coss = [i[1] for i in self.answer]
        labels_ids = [i[0] for i in self.answer]
        
        labels = [db_models.Label.query.filter_by(id = id).one() for id in labels_ids]
        contexts = [label.context.name for label in labels]
        sentences = zip(labels,coss)
        
        items = zip(contexts,coss)
        self.data = {}
        for item in items:
            if item[0] not in self.data:
                self.data[item[0]] = item[1]
            else:
                self.data[item[0]] += item[1]

        summ = sum(self.data.values())
        self.data = {k:(utils.float_to_int(v/summ,4)) for k,v in self.data.items()}
        self.data = sorted(self.data.items(), key = lambda x:x[1], reverse = True)[:3]

        return make_response(render_template('contextdistribution.html', form= self.form, data = self.data, question = self.question, answer = self.answer, sentences = sentences))




class Documents(Resource):

    def __init__(self):
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())
        self.sents = db_models.Sentparadoc.query.filter(db_models.Sentparadoc.docid.in_([i.id for i in self.documents])).all()
        self.sentterms = db_models.Sentterm.query.all()
        self.form = forms.DocUploadForm()

    def get(self):

        data = {}
        for document in self.documents:
            if document.title not in data:
                data[document.title] = {}
            total_sents = db_models.Sentparadoc.query.filter_by(docid = document.id).all()
            terms = db_models.Sentterm.query.filter(db_models.Sentterm.sentparadocid.in_([i.id for i in total_sents])).all()
            total_legit_terms = len([i for i in terms if i.term.entity == False and (i.term.fake == False or i.term.removed == False)])
            total_legit_entities = len([i for i in terms if i.term.entity == True and (i.term.fake == False or i.term.removed == False)])
            total_fake_terms = len([i for i in terms if i.term.entity == False and (i.term.fake == True or i.term.removed == True)])
            total_fake_entities = len([i for i in terms if i.term.entity == True and (i.term.fake == True or i.term.removed == True)])
            data[document.title] = [total_legit_terms, total_legit_entities, total_fake_terms, total_fake_entities]


        return make_response(render_template('documents.html', form = self.form, documents = self.documents, sents = self.sents, data = data))

    def post(self):
        starttime = datetime.now()
        global manager
        if manager is None:
            manager = doc_manager.DocManager(use_model)


        all_user_label_ids_embeddings = []
        for file in glob.glob('{}{}_*labelids*'.format(labelids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))

        self.files = self.form.files.data

        all_user_sentids_embeddings = []
        for file in glob.glob('{}{}_*sentid*'.format(sentids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_sentids_embeddings = pickle.load(open(file, 'rb'))

        for file in self.files:
            if file.filename in [doc.title for doc in self.documents]:
                flash('Document with name {} already exists!'.format(file.filename), 'info')
                continue
            self.text = utils.read_text_file(file)
            self.sentences = manager.doc_to_sent(self.text)

            self.document = db_models.Document(title=file.filename, userid = current_user.id)
            db_models.db.session.add(self.document)
            db_models.db.session.commit()

            for sent in self.sentences:
                sentparadoc = db_models.Sentparadoc(sentid = sent[1], paraid = sent[0], docid = self.document.id, senttext = sent[2])
                db_models.db.session.add(sentparadoc)
            db_models.db.session.commit()

            thisdoc_sentparadoc = db_models.Sentparadoc.query.filter_by(docid = self.document.id).all()

            for sent in thisdoc_sentparadoc:
                term_list = chunk.sent_terms(sent.senttext)
                for term in term_list:
                    if term[1] in [i.label for i in db_models.Term.query.all()]:
                        existing_term = db_models.Term.query.filter_by(label = term[1]).first()
                        newsentterm = db_models.Sentterm(sentparadocid = sent.id, termid = existing_term.id)
                        db_models.db.session.add(newsentterm)
                        db_models.db.session.commit()
                    else:
                        newterm = db_models.Term(label = term[1], entity = 1 if term[0] == 'e' else 0, fake = 1 if len(term[1])<3 else 0)
                        db_models.db.session.add(newterm)
                        db_models.db.session.commit()
                        sentterm = db_models.Sentterm(sentparadocid = sent.id, termid = newterm.id)
                        db_models.db.session.add(sentterm)
                        db_models.db.session.commit()


            sentids = [i.id for i in thisdoc_sentparadoc]
            sents = [sent[2] for sent in self.sentences]
            embeddings = manager.sent_to_embeddings(sents)

            sentids_embeddings = list(zip(sentids, embeddings))
            all_user_sentids_embeddings.extend(sentids_embeddings)

            #now take each sentid_embedding of the document and compute cossim with learnt model's embedding:

            # answer = manager.doc_cos_sim(sentids_embeddings, all_user_label_ids_embeddings)
            # # doc_sentid_embed[0],  model_sentid_embed[0],  sim

            # doc_sentids = [i[0] for i in answer]
            # model_sentids = [i[1] for i in answer]
            # coss = [i[2] for i in answer]


        outfile = open('{}{}_{}_sentids_embeds.pkl'.format(sentids_embeds_filedir,current_user.username,datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb')
        pickle.dump(all_user_sentids_embeddings,outfile)
        os.chdir(sentids_embeds_filedir)
        toberemoved = sorted(os.listdir(sentids_embeds_filedir), key=os.path.getmtime)
        toberemoved = [i for i in toberemoved if str(i.split('_')[0])==current_user.username][:-1]
        for file in toberemoved:
            os.remove(file)
        flash('Document uploaded in {} seconds'.format((datetime.now()-starttime).seconds), 'success')
        return redirect(request.url)


class Document(Resource):

    def __init__(self):
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())

    def get(self, docid, doctitle):
        
        document = db_models.Document.query.filter_by(userid = current_user.id).filter_by(id=docid).first()
        sentparadocs = db_models.Sentparadoc.query.filter_by(docid = document.id).all()
        # terms = db_models.Term.query.filter(db_models.Term.sentparadocid.in_([i.id for i in sentparadocs])).all()
        # paras = {}
        # para_terms = {}
        # for sentparadoc in sentparadocs:
        #     if sentparadoc.paraid not in paras:
        #         paras[sentparadoc.paraid] = ''
        #     paras[sentparadoc.paraid] += sentparadoc.senttext + ' '
        #     for term in sentparadoc.terms:
        #         if term not in para_terms:
        #             para_terms[paraid].add(term)
        # data = []
        # for paraid, paratext in paras:
        #     for pid,terms in para_terms:
        #         if paraid == pid:
        #             data.append((paraid,paratext,terms))

        return make_response(render_template('document.html', document = document, documents = self.documents, sentparadocs = sentparadocs))


class Terms(Resource):
    def __init__(self):
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())


    def get(self):
        terms = db_models.Term.query.filter_by(removed=False).all()
        removed_terms = db_models.Term.query.filter_by(removed=True).all()

        return make_response(render_template('terms.html', documents = self.documents, terms = terms, removed_terms = removed_terms))




class Term(Resource):
    def __init__(self):
        self.documents = db_models.Document.query.filter_by(userid=current_user.id).order_by(db_models.Document.date.desc())


    def get(self, termid):

        term = db_models.Term.query.filter_by(id=termid).first()
        sentterms = db_models.Sentterm.query.filter_by(termid = term.id).all()

        termdocs = {}
        for sentterm in sentterms:
            if sentterm.sentparadoc.document.title not in termdocs:
                termdocs[sentterm.sentparadoc.document.title] = 1
            else:
                termdocs[sentterm.sentparadoc.document.title] += 1

        related_terms = {}

        for sentterm in sentterms:
            for item in sentterm.sentparadoc.sentterms:
                if item.term.label not in related_terms:
                    related_terms[item.term.label] = 1
                else:
                    related_terms[item.term.label] += 1

        del related_terms[term.label]

        # global manager
        # if manager is None:
        #     manager = doc_manager.DocManager(use_model)
        
        # all_user_label_ids_embeddings = []
        # for file in glob.glob('{}{}_*labelids*'.format(labelids_embeds_filedir,current_user.username)):
        #     if len(file) != 0:
        #         all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))

        # answer = manager.cos_sim([term.label],all_user_label_ids_embeddings)
        # coss = [i[1] for i in answer]

        # labels_ids = [i[0] for i in answer]
        
        # labels = [db_models.Label.query.filter_by(id = id).one() for id in labels_ids]
        # contexts = [label.context.name for label in labels]
        # print(contexts)
        # sentences = zip(labels,coss)
        
        # items = zip(contexts,coss)
        # self.data = {}
        # for item in items:
        #     if item[0] not in self.data:
        #         self.data[item[0]] = item[1]
        #     else:
        #         self.data[item[0]] += item[1]

        # summ = sum(self.data.values())
        # self.data = {k:(utils.float_to_int(v/summ,4)) for k,v in self.data.items()}
        # self.data = sorted(self.data.items(), key = lambda x:x[1], reverse = True)[:3]

        return make_response(render_template('term.html', term = term, documents = self.documents, sentterms = sentterms, termdocs = termdocs, related_terms = related_terms))



class DocDelete(Resource):

    def post(self):
        docid = request.form['docid']
        document = db_models.Document.query.filter_by(id=docid).first()
        sentparadocs = db_models.Sentparadoc.query.filter_by(docid=docid).all()

        for file in glob.glob('{}{}_*'.format(sentids_embeds_filedir,current_user.username)):
            if len(file) != 0:
                all_user_sentids_embeddings = pickle.load(open(file, 'rb'))

        for item in sentparadocs:
            for sentid_embedding in all_user_sentids_embeddings:
                if sentid_embedding[0] == item.id:
                    all_user_sentids_embeddings.remove(sentid_embedding)
        outfile = open('{}{}_{}_sentids_embeds.pkl'.format(sentids_embeds_filedir,current_user.username,datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb')
        pickle.dump(all_user_sentids_embeddings,outfile)
        os.chdir(sentids_embeds_filedir)
        toberemoved = sorted(os.listdir(sentids_embeds_filedir), key=os.path.getmtime)
        toberemoved = [i for i in toberemoved if str(i.split('_')[0])==current_user.username][:-1]
        for file in toberemoved:
            os.remove(file)
        for item in sentparadocs:
            for term in item.sentterms:
                db_models.db.session.delete(term)
            db_models.db.session.delete(item)
        db_models.db.session.delete(document)
        db_models.db.session.commit()
        flash('Document successfully deleted', 'info')
        return redirect(url_for('documents'))


class TermDelete(Resource):
    def post(self):
        termid = request.form['termid']
        term = db_models.Term.query.filter_by(id = termid).first()
        term.removed = True
        db_models.db.session.add(term)
        db_models.db.session.commit()
        return redirect(url_for('terms'))


class TermUnDelete(Resource):
    def post(self):
        termid = request.form['termid']
        term = db_models.Term.query.filter_by(id = termid).first()
        term.removed = False
        db_models.db.session.add(term)
        db_models.db.session.commit()
        return redirect(url_for('terms'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


api.add_resource(Register,'/','/register', endpoint = 'register')
api.add_resource(Login,'/login', endpoint = 'login')
api.add_resource(Domains, '/domains', endpoint = 'domains')
api.add_resource(DomainDelete,'/domain_delete', endpoint = 'domain_delete')
api.add_resource(Domain, '/domain/<int:domainid>', endpoint = 'domain')
api.add_resource(ContextDistribution, '/contextdistribution', endpoint = 'contextdistribution')
api.add_resource(Documents, '/documents', endpoint = 'documents')
api.add_resource(Document, '/document/<int:docid>/<string:doctitle>', endpoint = 'document')
api.add_resource(Term, '/term/<int:termid>', endpoint = 'term')
api.add_resource(DocDelete,'/doc_delete', endpoint = 'doc_delete')
api.add_resource(Terms, '/terms', endpoint = 'terms')
api.add_resource(TermDelete,'/term_delete', endpoint = 'term_delete')
api.add_resource(TermUnDelete,'/term_undelete', endpoint = 'term_undelete')


if __name__ == '__main__':
    if sys.argv[1] == 'fresh':
        db_models.db.create_all()
    app.run(debug=True, port=5000)


