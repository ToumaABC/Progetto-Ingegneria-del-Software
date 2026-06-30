from app import db
from datetime import datetime,timezone

class AnnuncioSalvato(db.Model):
    __tablename__ = 'annuncio_salvato'
    
    studente_id = db.Column(db.Integer, db.ForeignKey('studente.id'), primary_key=True)
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), primary_key=True)
    
    annuncio = db.relationship('AnnuncioStanza', backref=db.backref('salvato_da_studenti', cascade="all, delete-orphan"))


class AnnuncioServizio(db.Model):
    __tablename__ = 'annuncio_servizio'
    
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), primary_key=True)
    servizio_id = db.Column(db.Integer, db.ForeignKey('servizio.id'), primary_key=True)
    
    annuncio = db.relationship('AnnuncioStanza', backref=db.backref('servizi_collegati', cascade="all, delete-orphan"))
    servizio = db.relationship('Servizio', backref=db.backref('annunci_collegati', cascade="all, delete-orphan"))

class AnnuncioStanza(db.Model):
    __tablename__ = 'annuncio_stanza'
    
    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    indirizzo = db.Column(db.String(255), nullable=False)
    descrizione = db.Column(db.Text, nullable=False)
    costo = db.Column(db.Float, nullable=False)
    
    visibile = db.Column(db.Boolean, default=True) 
    data_pubblicazione = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Chiave Esterna: il locatore che crea l'annuncio
    locatore_id = db.Column(db.Integer, db.ForeignKey('locatore.id'), nullable=False)
    
    # Relazione 1-a-Molti con FotoAnnuncio
    foto = db.relationship('FotoAnnuncio', backref='annuncio', lazy=True, cascade="all, delete-orphan")


class Servizio(db.Model):
    __tablename__ = 'servizio'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_servizio = db.Column(db.String(50), nullable=False, unique=True)
    
    def __repr__(self):
        return f"{self.nome_servizio}"
