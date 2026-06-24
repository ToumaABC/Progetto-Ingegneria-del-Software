from app import db
from app.GestioneStanza.models import AssociazioneStudenteStanza,StatoTicket,Ticket, Recensione
from app.GestioneUtente.gestore_utente import GestoreUtente
from app.GestioneFoto.models import FotoTicket
from app.GestioneFoto.gestore_foto import GestoreFoto

class GestoreStanza:

    @staticmethod
    def associaStudente(annuncio_id, email_studente):
        studente = GestoreUtente.cercaStudentePerEmail(email_studente)
        
        if not studente:
            raise ValueError("Nessuno studente trovato con questa email.")
            
        associazione_attiva = AssociazioneStudenteStanza.query.filter_by(studente_id=studente.id, attiva=True).first()
        if associazione_attiva:
            raise ValueError("Lo studente è già associato a un'altra stanza attiva.")
        
        associazione_disattivata = AssociazioneStudenteStanza.query.filter_by(studente_id=studente.id,annuncio_id=annuncio_id, attiva=False).first()
        if associazione_disattivata:
            associazione_disattivata.attiva = True
            db.session.commit()
            return associazione_disattivata
        

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
    
    @staticmethod
    def annullaAssociazione(annuncio_id, studente_id):
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id, 
            studente_id=studente_id,
            attiva=True
        ).first()
        
        if not associazione:
            raise ValueError("L'associazione specificata non esiste.")
        
        associazione.attiva = False

        db.session.commit()


    @staticmethod
    def get_associazione_attiva(annuncio_id, studente_id):
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=annuncio_id,
            studente_id=studente_id,
            attiva=True
        ).first()
        if not associazione:
            raise ValueError("Non sei associato a questa stanza.")
        return associazione

    @staticmethod
    def nuovoTicket(annuncio_id, studente_id, titolo, descrizione,files=None):
        associazione = GestoreStanza.get_associazione_attiva(annuncio_id, studente_id)

        ticket = Ticket(
            titolo=titolo,
            descrizione=descrizione,
            stato=StatoTicket.APERTO,
            associazione_id=associazione.id
        )
        db.session.add(ticket)

        db.session.flush()  

        if files:
            for file in files:
                if file and file.filename != '':
                    percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket.id)
                    if percorso:
                        foto = FotoTicket(percorso_file=percorso, ticket_id=ticket.id)
                        db.session.add(foto)


        db.session.commit()
        return ticket

    @staticmethod
    def visualizzaTicketStudente(studente_id):
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
    def modificaTicket(ticket_id, studente_id, titolo, descrizione,foto_da_aggiungere=None,foto_da_eliminare=None):
        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a modificare questo ticket.")

        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = FotoTicket.query.get(foto_id)
                if foto_check and foto_check.ticket_id == ticket.id:
                    print("AA") 
                    GestoreFoto.elimina_foto_db(foto_check)


        ticket.titolo = titolo
        ticket.descrizione = descrizione
        if foto_da_aggiungere:
            for file in foto_da_aggiungere:
                if file and file.filename != '':
                    percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket_id)
                    if percorso:
                        foto = FotoTicket(percorso_file=percorso, ticket_id=ticket_id)
                        db.session.add(foto)
                        print("AAA")

        db.session.commit()
        return ticket

    @staticmethod
    def eliminaTicket(ticket_id, studente_id):
        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questo ticket.")
    
        if ticket.stato != StatoTicket.APERTO:
            raise ValueError("Non è possibile eliminare un ticket in lavorazione o chiuso.")


        for foto in ticket.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)
        db.session.delete(ticket)
        db.session.commit()

    @staticmethod
    def aggiornaStatoTicket(ticket_id, locatore_id):
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
    

    @staticmethod
    def aggiungiFotoTicket(ticket_id, studente_id, files):
        """Salva una o più foto per un ticket."""


        ticket = Ticket.query.get_or_404(ticket_id)

        if ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato ad aggiungere foto a questo ticket.")

        foto_salvate = []
        for file in files:
            if file and file.filename != '':
                percorso = GestoreFoto.salva_file_fisico(file, 'tickets', 'ticket', ticket_id)
                if percorso:
                    foto = FotoTicket(percorso_file=percorso, ticket_id=ticket_id)
                    db.session.add(foto)
                    foto_salvate.append(foto)

        db.session.commit()
        return foto_salvate

    @staticmethod
    def eliminaFotoTicket(foto_id, studente_id):
        from app.GestioneFoto.models import FotoTicket
        from app.GestioneFoto.gestore_foto import GestoreFoto

        foto = FotoTicket.query.get_or_404(foto_id)

        if foto.ticket.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questa foto.")

        GestoreFoto.elimina_file_fisico(foto.percorso_file)
        db.session.delete(foto)
        db.session.commit()

    @staticmethod
    def aggiungiRecensione(annuncio_id, studente_id, titolo, descrizione, valutazione):
        associazione = GestoreStanza.get_associazione_attiva(annuncio_id, studente_id)

        if associazione.recensione:
            raise ValueError("Hai già pubblicato una recensione per questa stanza.")

        if not (1 <= int(valutazione) <= 5):
            raise ValueError("La valutazione deve essere compresa tra 1 e 5.")

        recensione = Recensione(
            titolo=titolo,
            descrizione=descrizione,
            valutazione=int(valutazione),
            associazione_id=associazione.id
        )
        db.session.add(recensione)
        db.session.commit()
        return recensione

    @staticmethod
    def visualizzaRecensioni(annuncio_id):
        """RF-27: Tutte le recensioni di un annuncio."""
        associazioni = AssociazioneStudenteStanza.query.filter_by(annuncio_id=annuncio_id).all()
        recensioni = [a.recensione for a in associazioni if a.recensione is not None]
        return recensioni

    @staticmethod
    def modificaRecensione(recensione_id, studente_id, titolo, descrizione, valutazione):

        recensione = Recensione.query.get_or_404(recensione_id)

        if recensione.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a modificare questa recensione.")

        if not (1 <= int(valutazione) <= 5):
            raise ValueError("La valutazione deve essere compresa tra 1 e 5.")

        recensione.titolo = titolo
        recensione.descrizione = descrizione
        recensione.valutazione = int(valutazione)
        db.session.commit()
        return recensione

    @staticmethod
    def eliminaRecensione(recensione_id, studente_id):

        recensione = Recensione.query.get_or_404(recensione_id)

        if recensione.associazione.studente_id != studente_id:
            raise ValueError("Non sei autorizzato a eliminare questa recensione.")

        db.session.delete(recensione)
        db.session.commit()

    @staticmethod
    def calcolaValutazioneMedia(annuncio_id):
        recensioni = GestoreStanza.visualizzaRecensioni(annuncio_id)
        if not recensioni:
            return None
        return round(sum(r.valutazione for r in recensioni) / len(recensioni), 1)