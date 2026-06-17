from app import db
from datetime import datetime

class Foto(db.Model):
    """
    Classe base astratta per le foto. 
    SQLAlchemy NON creerà una tabella 'foto', ma fornirà 
    questi attributi a tutte le classi che ereditano da essa.
    """
    __abstract__ = True     
    id_foto = db.Column(db.Integer, primary_key=True)
    percorso_file = db.Column(db.String(255), nullable=False) 

class FotoAnnuncio(Foto):
    """Tabella fisica per le foto collegate agli Annunci"""
    __tablename__ = 'foto_annuncio'
    
    # Chiave Esterna verso l'annuncio
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), nullable=False)


class FotoTicket(Foto):
    """ (Futura Implementazione)"""
    __tablename__ = 'foto_ticket'
