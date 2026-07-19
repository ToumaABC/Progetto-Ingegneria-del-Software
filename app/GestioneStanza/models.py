from app import db
from datetime import datetime,timezone
import enum

class AssociazioneStudenteStanza(db.Model):
    __tablename__ = 'associazione_studente_stanza'
    
    id = db.Column(db.Integer, primary_key=True)
    attiva = db.Column(db.Boolean, default=True) 
    
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), nullable=False)
    studente_id = db.Column(db.Integer, db.ForeignKey('studente.id'), nullable=False)
    
    # Relazioni
    annuncio = db.relationship('AnnuncioStanza', backref=db.backref('associazioni', lazy=True, cascade="all, delete-orphan"))
    studente = db.relationship('Studente', backref=db.backref('associazioni_stanze', lazy=True, cascade="all, delete-orphan"))


class StatoTicket(enum.Enum):
    APERTO = "aperto"
    IN_LAVORAZIONE = "in_lavorazione"
    CHIUSO = "chiuso"


class Ticket(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.String(1000), nullable=False)
    data_apertura = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    stato = db.Column(db.Enum(StatoTicket), default=StatoTicket.APERTO, nullable=False)

    associazione_id = db.Column(db.Integer, db.ForeignKey('associazione_studente_stanza.id'), nullable=False)

    # Relazioni
    associazione = db.relationship('AssociazioneStudenteStanza', backref=db.backref('tickets', lazy=True, cascade="all, delete-orphan"))
    foto = db.relationship('FotoTicket', lazy=True, cascade="all, delete-orphan")


class Recensione(db.Model):
    __tablename__ = 'recensione'

    id = db.Column(db.Integer, primary_key=True)
    titolo = db.Column(db.String(100), nullable=False)
    descrizione = db.Column(db.String(1000), nullable=False)
    valutazione = db.Column(db.Integer, nullable=False)  # 1-5
    data_pubblicazione = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    associazione_id = db.Column(db.Integer, db.ForeignKey('associazione_studente_stanza.id'), nullable=False)


    associazione = db.relationship('AssociazioneStudenteStanza',backref=db.backref('recensione', uselist=False, cascade="all, delete-orphan"))
