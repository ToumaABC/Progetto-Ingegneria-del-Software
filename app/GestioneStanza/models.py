from app import db
from datetime import datetime

class AssociazioneStudenteStanza(db.Model):
    __tablename__ = 'associazione_studente_stanza'
    
    id = db.Column(db.Integer, primary_key=True)
    attiva = db.Column(db.Boolean, default=True) 
    
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), nullable=False)
    studente_id = db.Column(db.Integer, db.ForeignKey('studente.id'), nullable=False)
    
    # Relazioni
    annuncio = db.relationship('AnnuncioStanza', backref=db.backref('associazioni', lazy=True, cascade="all, delete-orphan"))
    studente = db.relationship('Studente', backref=db.backref('associazioni_stanze', lazy=True, cascade="all, delete-orphan"))