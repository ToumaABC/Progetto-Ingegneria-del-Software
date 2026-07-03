from app import mail
from app.GestioneStanza.models import AssociazioneStudenteStanza, StatoTicket, Ticket, Recensione
from app.GestioneUtente.gestore_utente import GestoreUtente
from app.GestioneFoto.models import FotoTicket
from app.GestioneFoto.gestore_foto import GestoreFoto

class GestoreStanza:

    def __init__(self, db_instance):
        """Iniezione della dipendenza del database"""
        self.db = db_instance

    def associaStudente(self, annuncio_id, email_studente):
        # Istanzio il GestoreUtente passando il db corrente
        gestore_utente = GestoreUtente(self.db, mail)
        studente = gestore_utente.cercaStudentePerEmail(email_studente)
        
        if not studente:
            raise ValueError("Nessuno studente trovato con questa email.")
            
        associazione_attiva = AssociazioneStudenteStanza.query.filter_by(studente_id=studente.id, attiva=True).first()
        if associazione_attiva:
            raise ValueError("Lo studente è già associato a un'altra stanza attiva.")
        
        associazione_disattivata = AssociazioneStudenteStanza.query.filter_by(studente_id=studente.id, annuncio_id=annuncio_id, attiva=False).first()
        if associazione_disattivata:
            associazione_disattivata.attiva = True
            self.db.session.commit()
            return associazione_disattivata

        nuova_associazione = AssociazioneStudenteStanza(
            annuncio_id=annuncio_id,
            studente_id=studente.id,
            attiva=True
        )
        self.db.session.add(nuova_associazione)
        self.db.session.commit()
        return nuova_associazione

    def visualizzaInquilini(self, annuncio_id):
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id, attiva=True).all()
        return associazioni
    
    def annullaAssociazione(self, annuncio_id, studente_id):
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id, 
            studente_id=studente_id,
            attiva=True
        ).first()
        
        if not associazione:
            raise ValueError("L'associazione specificata non esiste.")
        
        associazione.attiva = False
        self.db.session.commit()

    def get_associazione_attiva(self, annuncio_id, studente_id):
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id,
            studente_id=studente_id,
            attiva=True
        ).first()
        if not associazione:
            raise ValueError("Non sei associato a questa stanza.")
        return associazione

    def nuovoTicket(self, annuncio_id, studente_id, titolo, descrizione, files=None):
        associazione = self.get_associazione_attiva(annuncio_id, studente_id)

        if not titolo or not descrizione:
            raise ValueError("Inserire almeno titolo e descrizione.")

        ticket = Ticket(
            titolo=titolo,
            descrizione=descrizione,
            stato=StatoTicket.APERTO,
            associazione_id=associazione.id
        )
        self.db.session.add(ticket)
        self.db.session.flush()  

        if files:
            for file in files:
                if file and file.filename != '':
                    try:
                        percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket.id)
                    except:
                        self.db.session.rollback()
                        raise
                    if percorso:
                        foto = FotoTicket(percorso_file=percorso, ticket_id=ticket.id)
                        self.db.session.add(foto)

        self.db.session.commit()
        return ticket

    def visualizzaTicketStudente(self, studente_id):
        associazioni = AssociazioneStudenteStanza.query.filter_by(studente_id=studente_id).all()
        tickets = []
        for a in associazioni:
            tickets.extend(a.tickets)
        return tickets

    def visualizzaTicketLocatore(self, annuncio_id):
        """Tutti i ticket relativi a un annuncio del locatore."""
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id).all()
        tickets = []
        for a in associazioni:
            tickets.extend(a.tickets)
        return tickets

    def modificaTicket(self, ticket_id, studente_id, titolo, descrizione, foto_da_aggiungere=None, foto_da_eliminare=None):
        ticket = self.db.session.get(Ticket, ticket_id)

        if not ticket:
            raise ValueError("Ticket non esiste.")

        if not titolo or not descrizione:
            raise ValueError("Inserire almeno titolo e descrizione")

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a modificare questo ticket.")

        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = FotoTicket.query.get(foto_id)
                if foto_check and foto_check.ticket_id == ticket.id:
                    GestoreFoto.elimina_foto_db(foto_check)

        ticket.titolo = titolo
        ticket.descrizione = descrizione
        if foto_da_aggiungere:
            for file in foto_da_aggiungere:
                if file and file.filename != '':
                    try:
                        percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket_id)
                    except:
                        raise
                    if percorso:
                        foto = FotoTicket(percorso_file=percorso, ticket_id=ticket_id)
                        self.db.session.add(foto)

        self.db.session.commit()
        return ticket

    def eliminaTicket(self, ticket_id, studente_id):
        ticket = self.db.session.get(Ticket, ticket_id)

        if not ticket:
            raise ValueError("Ticket non esiste.")

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questo ticket.")
    
        if ticket.stato != StatoTicket.APERTO:
            raise ValueError("Non è possibile eliminare un ticket in lavorazione o chiuso.")

        for foto in ticket.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)
        self.db.session.delete(ticket)
        self.db.session.commit()

    def aggiornaStatoTicket(self, ticket_id, locatore_id):
        ticket = self.db.session.get(Ticket, ticket_id)

        if not ticket:
            raise ValueError("Ticket non esiste.")

        # Verifica che il ticket appartenga a un annuncio del locatore
        if ticket.associazione.annuncio.locatore_id != locatore_id:
            raise ValueError("Non sei autorizzato ad aggiornare questo ticket.")

        if ticket.stato == StatoTicket.APERTO:
            ticket.stato = StatoTicket.IN_LAVORAZIONE
        elif ticket.stato == StatoTicket.IN_LAVORAZIONE:
            ticket.stato = StatoTicket.CHIUSO
        else:
            raise ValueError("Il ticket è già chiuso.")

        self.db.session.commit()
        return ticket
    
    def aggiungiFotoTicket(self, ticket_id, studente_id, files):
        """Salva una o più foto per un ticket."""
        ticket = self.db.session.get(Ticket, ticket_id)
        if not ticket:
            raise ValueError("Ticket non trovato.")

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato ad aggiungere foto a questo ticket.")

        foto_salvate = []
        for file in files:
            if file and file.filename != '':
                percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket_id)
                if percorso:
                    foto = FotoTicket(percorso_file=percorso, ticket_id=ticket_id)
                    self.db.session.add(foto)
                    foto_salvate.append(foto)

        self.db.session.commit()
        return foto_salvate

    def eliminaFotoTicket(self, foto_id, studente_id):
        foto = FotoTicket.query.get(foto_id)
        if not foto:
            raise ValueError("Foto non trovata.")

        if foto.ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questa foto.")

        GestoreFoto.elimina_file_fisico(foto.percorso_file)
        self.db.session.delete(foto)
        self.db.session.commit()

    def aggiungiRecensione(self, annuncio_id, studente_id, titolo, descrizione, valutazione):
        associazione = self.get_associazione_attiva(annuncio_id, studente_id)

        if associazione.recensione:
            raise ValueError("Hai già pubblicato una recensione per questa stanza.")

        if not titolo or not descrizione or not valutazione:
            raise ValueError("Compila tutti i campi")

        if not (1 <= int(valutazione) <= 5):
            raise ValueError("La valutazione deve essere compresa tra 1 e 5.")

        recensione = Recensione(
            titolo=titolo,
            descrizione=descrizione,
            valutazione=int(valutazione),
            associazione_id=associazione.id
        )
        self.db.session.add(recensione)
        self.db.session.commit()
        return recensione

    def visualizzaRecensioni(self, annuncio_id):
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id).all()
        recensioni = [a.recensione for a in associazioni if a.recensione is not None]
        return recensioni

    def modificaRecensione(self, recensione_id, studente_id, titolo, descrizione, valutazione):
        recensione = self.db.session.get(Recensione, recensione_id)

        if not recensione:
            raise ValueError("Recensione non trovata")

        if not titolo or not descrizione or not valutazione:
            raise ValueError("Compila tutti i campi")

        if recensione.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a modificare questa recensione.")

        if not (1 <= int(valutazione) <= 5):
            raise ValueError("La valutazione deve essere compresa tra 1 e 5.")

        recensione.titolo = titolo
        recensione.descrizione = descrizione
        recensione.valutazione = int(valutazione)
        self.db.session.commit()
        return recensione

    def eliminaRecensione(self, recensione_id, studente_id):
        recensione = self.db.session.get(Recensione, recensione_id)

        if not recensione:
            raise ValueError("Recensione non trovata")

        if recensione.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questa recensione.")

        self.db.session.delete(recensione)
        self.db.session.commit()

    def calcolaValutazioneMedia(self, annuncio_id):
        recensioni = self.visualizzaRecensioni(annuncio_id)
        if not recensioni:
            return None
        return round(sum(r.valutazione for r in recensioni) / len(recensioni), 1)

    def getRecensioneById(self, id):
        return self.db.session.get(Recensione, id)