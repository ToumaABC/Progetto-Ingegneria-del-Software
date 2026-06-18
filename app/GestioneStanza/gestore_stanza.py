from app import db
from app.GestioneUtente.models import Studente
from app.GestioneStanza.models import AssociazioneStudenteStanza
from app.GestioneUtente.gestore_utente import GestoreUtente


class GestoreStanza:

    @staticmethod
    def associaStudente(annuncio_id, email_studente):
        studente = GestoreUtente.cercaStudentePerEmail(email_studente)
        
        if not studente:
            raise ValueError("Nessuno studente trovato con questa email.")
            
        associazione_attiva = AssociazioneStudenteStanza.query.filter_by(studente_id=studente.id, attiva=True).first()
        if associazione_attiva:
            raise ValueError("Lo studente è già associato a un'altra stanza attiva.")
            
        nuova_associazione = AssociazioneStudenteStanza(
            annuncio_id=annuncio_id,
            studente_id=studente.id,
            attiva=True
        )
        db.session.add(nuova_associazione)
        db.session.commit()
        return nuova_associazione

    @staticmethod
    def visualizzaInquilini(annuncio_id):
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id, attiva=True).all()
        return associazioni
    

    def annullaAssociazione(annuncio_id, studente_id):
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id, 
            studente_id=studente_id
        ).first()
        
        if not associazione:
            raise ValueError("L'associazione specificata non esiste.")
            
        # Il caso d'uso dice: "scollega i dati nel database"
        db.session.delete(associazione)
        db.session.commit()