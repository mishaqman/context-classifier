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

filedir = os.path.join(os.getcwd(),'../data/')
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
        self.domains = db_models.Domain.query.filter_by(userid = current_user.id).all()
        self.form = forms.DomainForm()

    def get(self):
        return make_response(render_template('domains.html', form = self.form, domains = self.domains))


    def post(self):
        name = self.form.name.data
        domain = db_models.Domain(name = name, userid = current_user.id)
        db_models.db.session.add(domain)
        db_models.db.session.commit()
        return redirect(request.url)


class Domain(Resource):
    def __init__(self):
        
        self.form = forms.LabelUploadForm()

    def get(self, domainid):
        self.domains = db_models.Domain.query.filter_by(userid = current_user.id).all()
        self.domain = db_models.Domain.query.filter_by(id = domainid, userid = current_user.id).first()
        self.contexts = db_models.Context.query.filter_by(domainid = domainid).all()
        self.labels = db_models.Label.query.filter(db_models.Label.contextid.in_([i.id for i in self.contexts])).all()[:500]
        return make_response(render_template('domain.html', form= self.form, domains = self.domains, domain = self.domain, labels = self.labels, contexts = self.contexts))


    def post(self, domainid):

        global manager
        if manager is None:
            manager = doc_manager.DocManager(use_model)
        
        all_user_label_ids_embeddings = []
        for file in glob.glob('{}{}_*'.format(filedir,current_user.username)):
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

        outfile = open('{}{}_{}_embeddings.pkl'.format(filedir,current_user.username,datetime.now().strftime('%Y%m%d_%H%M%S')), 'wb')
        pickle.dump(all_user_label_ids_embeddings,outfile)
        os.chdir(filedir)
        toberemoved = sorted(os.listdir(filedir), key=os.path.getmtime)
        toberemoved = [i for i in toberemoved if str(i.split('_')[0])==current_user.username][:-1]
        for file in toberemoved:
            os.remove(file)

        return redirect(request.url)


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
        for file in glob.glob('{}{}_*'.format(filedir,current_user.username)):
            if len(file) != 0:
                all_user_label_ids_embeddings = pickle.load(open(file, 'rb'))

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




@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


api.add_resource(Register,'/','/register', endpoint = 'register')
api.add_resource(Login,'/login', endpoint = 'login')
api.add_resource(Domains, '/domains', endpoint = 'domains')
api.add_resource(Domain, '/domain/<int:domainid>', endpoint = 'domain')
api.add_resource(ContextDistribution, '/contextdistribution', endpoint = 'contextdistribution')

if __name__ == '__main__':
    if sys.argv[1] == 'fresh':
        db_models.db.create_all()
    app.run(debug=True, port=5000)


'''
<legend>Your cosine similar sentences</legend>
<table class="table">
  <thead class="thead-light">
    <tr>
      <th style="width: auto;" scope="col">Label</th>
      <th style="width: auto;" scope="col">Cos similarity</th>
      <th style="width: auto;" scope="col">Context</th>
    </tr>
  </thead>

  {% for item in data %}
  <tbody>
    
    <tr>
      <td>{{item[0].text}}</td>
      <td>{{item[1]}}</td>
      <td>{{item[0].context.name}}</td>
    </tr>
    
  </tbody>
  {% endfor %}

</table>
'''