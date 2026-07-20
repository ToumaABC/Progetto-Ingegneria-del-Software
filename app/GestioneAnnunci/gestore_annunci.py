from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, AnnuncioServizio, AnnuncioSalvato
from app.GestioneFoto.models import FotoAnnuncio
from app.GestioneFoto.gestore_foto import GestoreFoto
from sqlalchemy import select, delete

from app.GestioneStanza.models import Recensione


class GestoreAnnunci:


    def __init__(self, db,gestore_stanza):
        self.db = db
        self.gestore_stanza = gestore_stanza

    def aggiungiAnnuncio(self,dati, servizi, file_foto, locatore_id):
        titolo = dati.get("titolo")
        indirizzo = dati.get("indirizzo")
        descrizione = dati.get("descrizione")
        costo = dati.get("costo")

        if not titolo or not indirizzo or not descrizione or not costo:
            raise ValueError("Compila tutti i campi obbligatori.")

        try:
            costo_f = float(costo)
        except (ValueError,TypeError):
            raise ValueError("Il costo deve essere un numero con la virgola")

        #Controllo se ho inserito una foto
        if not file_foto or file_foto[0].filename == "":
             raise ValueError("È richiesta almeno una foto per l'annuncio.")

        GestoreFoto.valida_lista_file(file_foto)

        # Creazione Annuncio
        nuovo_annuncio = AnnuncioStanza(
            titolo=titolo,
            indirizzo=indirizzo,
            descrizione=descrizione,
            costo=costo_f,
            locatore_id=locatore_id
        )
        self.db.session.add(nuovo_annuncio)
        #Faccio il flush per ottenere l"id dell"annuncio
        self.db.session.flush()

        # Gestione Servizi
        servizi_selezionati = servizi
        for serv_id in servizi_selezionati:
            servizio = self.db.session.get(Servizio,serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=nuovo_annuncio.id, servizio_id=servizio.id)
                self.db.session.add(annuncio_servizio)

        for file in file_foto:
            percorso = GestoreFoto.salva_file_fisico(file, "annunci", "annuncio", nuovo_annuncio.id)
            if percorso:
                nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=nuovo_annuncio.id)
                self.db.session.add(nuova_foto)

        self.db.session.commit()
        return nuovo_annuncio

    def modificaAnnuncio(self,annuncio, servizi, dati, file_foto=None, foto_da_eliminare=None):

        titolo = dati.get("titolo", annuncio.titolo)
        indirizzo = dati.get("indirizzo", annuncio.indirizzo)
        descrizione = dati.get("descrizione", annuncio.descrizione)

        if not titolo or not indirizzo or not descrizione:
            raise ValueError("Compila i campi che vuoi modificare con valori validi")

        costo = dati.get("costo")
        costo_f = annuncio.costo
        if costo:
            try:
                costo_f = float(costo)
            except (ValueError,TypeError):
                raise ValueError("Il costo deve essere un numero con la virgola")

        # Conto quante foto nuove verranno effettivamente caricate
        nuove_foto_valide = [f for f in file_foto if f and f.filename] if file_foto else []

        GestoreFoto.valida_lista_file(nuove_foto_valide)

        # Recupero le foto da eliminare che sono effettivamente valide (esistenti e appartenenti all"annuncio)
        foto_da_eliminare_valide = []
        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = self.db.session.get(FotoAnnuncio, foto_id)
                if foto_check and foto_check.annuncio_id == annuncio.id:
                    foto_da_eliminare_valide.append(foto_check)

        # Controllo che dopo la modifica rimanga almeno una foto per l"annuncio
        foto_totali_dopo_modifica = len(annuncio.foto) - len(foto_da_eliminare_valide) + len(nuove_foto_valide)
        if foto_totali_dopo_modifica < 1:
            raise ValueError("L'annuncio deve avere almeno una foto.")


        #Modifico il db
        annuncio.titolo = titolo
        annuncio.indirizzo = indirizzo
        annuncio.descrizione = descrizione
        annuncio.costo = costo_f

        if nuove_foto_valide:
            for file in nuove_foto_valide:
                percorso = GestoreFoto.salva_file_fisico(file, sotto_cartella="annunci", prefisso_nome="annuncio",id_entita=annuncio.id)
                if percorso:
                    nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=annuncio.id)
                    self.db.session.add(nuova_foto)

        if foto_da_eliminare_valide:
            for foto_check in foto_da_eliminare_valide:
                GestoreFoto.elimina_file_fisico(foto_check.percorso_file)
                self.db.session.delete(foto_check)


        servizi_selezionati = servizi
        #Elimino i servizi assocaiti all'annuncio e creo le nuove associazioni annuncio servizio
        self.db.session.execute(delete(AnnuncioServizio).filter_by(annuncio_id=annuncio.id))
        for serv_id in servizi_selezionati:
            servizio = self.db.session.get(Servizio, serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=annuncio.id, servizio_id=servizio.id)
                self.db.session.add(annuncio_servizio)

        self.db.session.commit()

    def eliminaAnnuncio(self,annuncio):
        for foto in annuncio.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)

        for associazione in annuncio.associazioni:
            for ticket in associazione.tickets:
                for foto_ticket in ticket.foto:
                    GestoreFoto.elimina_file_fisico(foto_ticket.percorso_file)

        self.db.session.delete(annuncio)
        self.db.session.commit()

    def cambiaVisibilita(self,annuncio):
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
        annuncio.visibile = not annuncio.visibile
        self.db.session.commit()
        return annuncio.visibile

    def visualizzaAnnuncio(self, id_annuncio):
        annuncio = self.db.session.get(AnnuncioStanza, id_annuncio)
        if not annuncio or annuncio.visibile== False:
            raise ValueError("Annuncio non trovato.")
        inquilini = self.gestore_stanza.visualizzaInquilini(id_annuncio)
        recensioni = self.gestore_stanza.visualizzaRecensioni(id_annuncio)
        media_voto = self.gestore_stanza.calcolaValutazioneMedia(id_annuncio)

        return {
            "annuncio": annuncio,
            "locatore": annuncio.locatore,
            "inquilini": inquilini,
            "recensioni": recensioni,
            "media_voto": media_voto
        }

    def ricercaAnnunci(self, query_testo=None, prezzo_max=None, servizi_selezionati=None):

        annunci = select(AnnuncioStanza).filter_by(visibile=True)

        # Flusso principale ricerca
        if query_testo:
            search = f"%{query_testo}%"
            annunci = annunci.filter(
                self.db.or_(
                    AnnuncioStanza.indirizzo.ilike(search),
                    AnnuncioStanza.titolo.ilike(search),
                    AnnuncioStanza.descrizione.ilike(search)
                )
            )

        # Punto di estensione se ci sono filtri
        if prezzo_max or servizi_selezionati:
            annunci = self.filtraAnnunci(annunci, prezzo_max, servizi_selezionati)

        return self.db.session.scalars(annunci).all()

    def filtraAnnunci(self, l_annunci, prezzo_max=None, servizi_selezionati=None):
        try:
            prezzo = float(prezzo_max)
            l_annunci = l_annunci.filter(AnnuncioStanza.costo <= prezzo)
        except (TypeError,ValueError):
            pass # Se il valore non è numerico, restituisce la query inalterata
        
        if servizi_selezionati:
            # Per ogni servizio selezionato, obblighiamo l"annuncio a possederlo
            for serv_id in servizi_selezionati:
                try:
                    id_serv = int(serv_id)
                    subquery = select(AnnuncioServizio.annuncio_id).filter(AnnuncioServizio.servizio_id == id_serv)
                    l_annunci = l_annunci.filter(AnnuncioStanza.id.in_(subquery))
                except ValueError:
                    pass
                
        return l_annunci

    def salvaAnnuncio(self,studente_id, annuncio_id):
        annuncio = self.db.session.get(AnnuncioStanza, annuncio_id)

        if not annuncio or not annuncio.visibile:
            raise ValueError("Annuncio non trovato o non disponibile.")

        salvataggio_esistente = self.db.session.scalar(select(AnnuncioSalvato).filter_by(studente_id=studente_id, annuncio_id=annuncio_id))
        if salvataggio_esistente:
            raise ValueError("Hai già salvato questo annuncio.")
        nuovo_salvataggio = AnnuncioSalvato(studente_id=studente_id, annuncio_id=annuncio_id)
        self.db.session.add(nuovo_salvataggio)
        self.db.session.commit()

    def eliminaAnnuncioSalvato(self,studente_id, annuncio_id):
        annuncio = self.db.session.get(AnnuncioStanza, annuncio_id)

        if not annuncio or not annuncio.visibile:
            raise ValueError("Annuncio non trovato o non disponibile.")


        salvataggio = self.db.session.scalar(select(AnnuncioSalvato).filter_by(studente_id=studente_id, annuncio_id=annuncio_id))
        if not salvataggio:
            raise ValueError("Non puoi rimuovere un annuncio non salvato ")
        self.db.session.delete(salvataggio)
        self.db.session.commit()

    def getListaServizi(self):
        return self.db.session.scalars(select(Servizio)).all()

    def verificaProprietaAnnuncio(self, annuncio_id, utente_id):
        annuncio = self.db.session.get(AnnuncioStanza, annuncio_id)
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
            
        if annuncio.locatore_id != utente_id:
            raise ValueError("Azione non autorizzata. Non sei il proprietario di questo annuncio.")
            
        return annuncio


