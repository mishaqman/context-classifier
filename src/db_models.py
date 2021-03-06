from app import app
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
import enum



# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:mishaq@localhost/abis'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/c/Users/ishaq/Desktop/Projects/context-classifier/data/cclassifier.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    joining_date = db.Column(db.DateTime, nullable = False, default = datetime.now)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    documents = db.relationship('Document', backref='user', lazy=True)
    domains = db.relationship('Domain', backref='user', lazy=True)


class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    contexts = db.relationship('Context', backref='domain', lazy=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)



class Context(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    labels = db.relationship('Label', backref='context', lazy=True)
    domainid = db.Column(db.Integer, db.ForeignKey('domain.id'), nullable=False)


class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(2000), nullable=False)
    embedding = db.Column(db.Boolean, default=False, nullable=False)
    contextid = db.Column(db.Integer, db.ForeignKey('context.id'), nullable=False)



class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    sentparadocs = db.relationship('Sentparadoc', backref='document', lazy=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


class Sentparadoc(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sentid = db.Column(db.Integer, nullable=False)
    paraid = db.Column(db.Integer, nullable=False)
    docid = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    senttext = db.Column(db.String(1000), nullable=False)
    sentterms = db.relationship('Sentterm', backref='sentparadoc', lazy=True)


class TermType(enum.Enum):
    entity = 0
    noun = 1
    mnp = 2


class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(1000), nullable=False)
    termtype = db.Column(db.Enum(TermType), default=False, nullable=False)
    fake = db.Column(db.Boolean, default=False, nullable=False)
    removed = db.Column(db.Boolean, default=False, nullable=False)
    sentterms = db.relationship('Sentterm', backref='term', lazy=True)


class Termchild(db.Model):
    parentid = db.Column(db.Integer, nullable=False, primary_key=True)
    childid = db.Column(db.Integer, nullable=False, primary_key=True)


class EquivalentTerm(db.Model):
    basetermid = db.Column(db.Integer, nullable=False, primary_key=True)
    equivalentid = db.Column(db.Integer, nullable=False, primary_key=True)


class Sentterm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sentparadocid = db.Column(db.Integer, db.ForeignKey('sentparadoc.id'), nullable=False)
    termid = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=False)
    equivalentid = db.Column(db.Integer, nullable=True)
    duplicate = db.Column(db.Boolean, default=False, nullable=False)
