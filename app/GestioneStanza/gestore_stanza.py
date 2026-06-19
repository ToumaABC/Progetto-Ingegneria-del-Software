from app import db
from app.GestioneStanza.models import AssociazioneStudenteStanza,StatoTicket,Ticket
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


    @staticmethod
    def _get_associazione_attiva(annuncio_id, studente_id):
        """Restituisce l'associazione attiva tra studente e annuncio, o solleva ValueError."""
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id,
            studente_id=studente_id,
            attiva=True
        ).first()
        if not associazione:
            raise ValueError("Non sei associato a questa stanza.")
        return associazione

    @staticmethod
    def nuovoTicket(annuncio_id, studente_id, titolo, descrizione):
        associazione = GestoreStanza._get_associazione_attiva(annuncio_id, studente_id)

        ticket = Ticket(
            titolo=titolo,
            descrizione=descrizione,
            stato=StatoTicket.APERTO,
            associazione_id=associazione.id
        )
        db.session.add(ticket)
        db.session.commit()
        return ticket

    @staticmethod
    def visualizzaTicketStudente(studente_id):
        """Tutti i ticket aperti dallo studente (su qualsiasi stanza)."""
        associazioni = AssociazioneStudenteStanza.query.filter_by(studente_id=studente_id).all()
        tickets = []
        for a in associazioni:
            tickets.extend(a.tickets)
        return tickets

    @staticmethod
    def visualizzaTicketLocatore(annuncio_id):
        """Tutti i ticket relativi a un annuncio del locatore."""
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id).all()
        tickets = []
        for a in associazioni:
            tickets.extend(a.tickets)
        return tickets

    @staticmethod
    def modificaTicket(ticket_id, studente_id, titolo, descrizione):
        ticket = Ticket.query.get_or_404(ticket_id)

        # Solo lo studente che ha aperto il ticket può modificarlo
        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a modificare questo ticket.")

        ticket.titolo = titolo
        ticket.descrizione = descrizione
        db.session.commit()
        return ticket

    @staticmethod
    def eliminaTicket(ticket_id, studente_id):
        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questo ticket.")

        db.session.delete(ticket)
        db.session.commit()

    @staticmethod
    def aggiornaStatoTicket(ticket_id, locatore_id):
        """Il locatore fa avanzare lo stato: APERTO → IN_LAVORAZIONE → CHIUSO."""
        ticket = Ticket.query.get_or_404(ticket_id)

        # Verifica che il ticket appartenga a un annuncio del locatore
        if ticket.associazione.annuncio.locatore_id != locatore_id:
            raise ValueError("Non sei autorizzato ad aggiornare questo ticket.")

        if ticket.stato == StatoTicket.APERTO:
            ticket.stato = StatoTicket.IN_LAVORAZIONE
        elif ticket.stato == StatoTicket.IN_LAVORAZIONE:
            ticket.stato = StatoTicket.CHIUSO
        else:
            raise ValueError("Il ticket è già chiuso.")

        db.session.commit()
        return ticket