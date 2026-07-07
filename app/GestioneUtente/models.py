from app import db
from flask_login import UserMixin
from sqlalchemy import select


class Utente(UserMixin, db.Model):
    __tablename__ = 'utente'
    
    # Attributi diagramma delle classi
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    cognome = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False) # RNF-4 Unicità email
    numTelefono = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(255), nullable=False) # RNF-2 Password criptata
    ruolo = db.Column(db.String(20), nullable=False)
    verificato = db.Column(db.Boolean, default=False)

    # Direttiva SQLAlchemy per specficare come gestire il polimorfismo(Cosa istanziare tra Studente e Locatore)
    __mapper_args__ = {
        'polymorphic_on': ruolo,
        'polymorphic_identity': 'utente'
    }

    @classmethod
    def cercaUtentePerEmail(cls, email_inserita):
        return db.session.scalar(select(cls).filter_by(email=email_inserita))

class Studente(Utente):
    __tablename__ = 'studente'
    id = db.Column(db.Integer, db.ForeignKey('utente.id'), primary_key=True)
    
    # Attributi specifici
    corso = db.Column(db.String(100), nullable=True)
    facolta = db.Column(db.String(100), nullable=True)
    universita = db.Column(db.String(100), nullable=True)

    salvataggi = db.relationship('AnnuncioSalvato', backref='studente', lazy=True, cascade="all, delete-orphan")


    def getListaAnnunciSalvati(self):
        lista_annunci_salvati = []
        for salvataggio in self.salvataggi:
            if(salvataggio.annuncio.visibile==True):
                lista_annunci_salvati.append(salvataggio.annuncio)
        return lista_annunci_salvati

    def getAssociazioneAttiva(self):
        for associazione in self.associazioni_stanze:
            if associazione.attiva:
                return associazione
        return None

    def associatoAllaStanza(self, annuncio_id):
        for associazione in self.associazioni_stanze:
            if associazione.annuncio_id == annuncio_id and associazione.attiva:
                return associazione
        return None

    def haRecensitoAnnuncio(self, annuncio_id):
        for associazione in self.associazioni_stanze:
            if associazione.annuncio_id == annuncio_id and associazione.recensione is not None:
                return True
        return False

    __mapper_args__ = {
        'polymorphic_identity': 'studente'
    }

class Locatore(Utente):
    __tablename__ = 'locatore'
    id = db.Column(db.Integer, db.ForeignKey('utente.id'), primary_key=True)

    annunci = db.relationship(
        'AnnuncioStanza', 
        backref='locatore', 
        lazy=True, 
        cascade="all, delete-orphan"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'locatore'
    }