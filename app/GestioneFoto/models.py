from app import db

class Foto(db.Model):
    __abstract__ = True
    id_foto = db.Column(db.Integer, primary_key=True)
    percorso_file = db.Column(db.String(255), nullable=False) 

class FotoAnnuncio(Foto):
    __tablename__ = 'foto_annuncio'
    
    annuncio_id = db.Column(db.Integer, db.ForeignKey('annuncio_stanza.id'), nullable=False)


class FotoTicket(Foto):
    __tablename__ = 'foto_ticket'
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

