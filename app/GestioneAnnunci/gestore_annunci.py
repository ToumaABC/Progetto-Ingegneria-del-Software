from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, AnnuncioServizio, AnnuncioSalvato
from app.GestioneFoto.models import FotoAnnuncio
from app.GestioneFoto.gestore_foto import GestoreFoto


class GestoreAnnunci:


    def __init__(self, db,gestore_utente,gestore_stanza):
        self.db = db
        self.gestore_utente = gestore_utente
        self.gestore_stanza = gestore_stanza

    def aggiungiAnnuncio(self,dati, servizi, file_foto, locatore_id):
        titolo = dati.get("titolo")
        indirizzo = dati.get("indirizzo")
        descrizione = dati.get("descrizione")
        costo = dati.get("costo")

        if not titolo or not indirizzo or not descrizione or not costo:
            raise ValueError("Compila tutti i campi obbligatori.")

        # Creazione Annuncio
        nuovo_annuncio = AnnuncioStanza(
            titolo=titolo,
            indirizzo=indirizzo,
            descrizione=descrizione,
            costo=float(costo),
            locatore_id=locatore_id
        )
        self.db.session.add(nuovo_annuncio)
        #Faccio il flush per ottenere l"id dell"annuncio
        self.db.session.flush()

        # Gestione Servizi
        servizi_selezionati = servizi
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=nuovo_annuncio.id, servizio_id=servizio.id)
                self.db.session.add(annuncio_servizio)

        # Gestione Foto
        if not file_foto or file_foto[0].filename == "":
             raise ValueError("È richiesta almeno una foto per l'annuncio.")


        for file in file_foto:
            percorso = GestoreFoto.salva_file_fisico(file, "annunci", "annuncio", nuovo_annuncio.id)
            if percorso:
                nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=nuovo_annuncio.id)
                self.db.session.add(nuova_foto)

        self.db.session.commit()
        return nuovo_annuncio

    def modificaAnnuncio(self,annuncio, servizi, dati, file_foto=None, foto_da_eliminare=None):

        # 1. Aggiornamento dei campi testuali
        annuncio.titolo = dati.get("titolo", annuncio.titolo)
        annuncio.indirizzo = dati.get("indirizzo", annuncio.indirizzo)
        annuncio.descrizione = dati.get("descrizione", annuncio.descrizione)
        
        costo = dati.get("costo")
        if costo:
            annuncio.costo = float(costo)


        if file_foto:
            for file in file_foto:
                percorso = GestoreFoto.salva_file_fisico(file, sotto_cartella="annunci", prefisso_nome="annuncio", id_entita=annuncio.id)
                if percorso:
                    nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=annuncio.id)
                    self.db.session.add(nuova_foto)

        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = FotoAnnuncio.query.get(foto_id)
                if foto_check and foto_check.annuncio_id == annuncio.id:
                    GestoreFoto.elimina_file_fisico(foto_check.percorso_file)
                    self.db.session.delete(foto_check)

        servizi_selezionati = servizi
        AnnuncioServizio.query.filter_by(annuncio_id=annuncio.id).delete()
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=annuncio.id, servizio_id=servizio.id)
                self.db.session.add(annuncio_servizio)

        self.db.session.commit()

    def eliminaAnnuncio(self,annuncio_id,user_id):
        annuncio = self.verificaProprietaAnnuncio(annuncio_id, user_id)
        for foto in annuncio.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)
        self.db.session.delete(annuncio)
        self.db.session.commit()

    def cambiaVisibilita(self,annuncio):
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
        annuncio.visibile = not annuncio.visibile
        self.db.session.commit()
        return annuncio.visibile

    def visualizza_annuncio(self,id_annuncio):
        annuncio = self.db.session.get(AnnuncioStanza, id_annuncio)
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
        locatore = self.gestore_utente.visualizzaProfilo(annuncio.locatore_id)
        inquilini = self.gestore_stanza.visualizzaInquilini(id_annuncio)
        recensioni = self.gestore_stanza.visualizzaRecensioni(id_annuncio)
        media_voto = self.gestore_stanza.calcolaValutazioneMedia(id_annuncio)

        return {
            "annuncio": annuncio,
            "locatore": locatore,
            "inquilini": inquilini,
            "recensioni": recensioni,
            "media_voto": media_voto
        }

    def ricerca_annunci(self,query_testo=None, prezzo_max=None, servizi_selezionati=None):

        annunci = AnnuncioStanza.query.filter_by(visibile=True)

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
            annunci = self.filtra_annunci(annunci, prezzo_max,servizi_selezionati)
            
        return annunci.all()

    def filtra_annunci(self,l_annunci, prezzo_max=None, servizi_selezionati=None):
        try:
            prezzo = float(prezzo_max)
            l_annunci = l_annunci.filter(AnnuncioStanza.costo <= prezzo)
        except TypeError:
            pass # Se il valore non è numerico, restituisce la query inalterata
        
        if servizi_selezionati:
            # Per ogni servizio selezionato, obblighiamo l"annuncio a possederlo
            for serv_id in servizi_selezionati:
                try:
                    id_serv = int(serv_id)
                    subquery = self.db.session.query(AnnuncioServizio.annuncio_id).filter(AnnuncioServizio.servizio_id == id_serv)
                    l_annunci = l_annunci.filter(AnnuncioStanza.id.in_(subquery))
                except ValueError:
                    pass
                
        return l_annunci

    def salvaAnnuncio(self,studente_id, annuncio_id):
        if not AnnuncioStanza.query.get(annuncio_id) :
            raise ValueError("Annuncio non trovato.")
        salvataggio_esistente = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if salvataggio_esistente:
            raise ValueError("Hai già salvato questo annuncio.")
        nuovo_salvataggio = AnnuncioSalvato(studente_id=studente_id, annuncio_id=annuncio_id)
        self.db.session.add(nuovo_salvataggio)
        self.db.session.commit()

    def eliminaAnnuncioSalvato(self,studente_id, annuncio_id):
        salvataggio = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if not salvataggio:
            raise ValueError("Non puoi rimuovere un annuncio non salvato ")
        self.db.session.delete(salvataggio)
        self.db.session.commit()

    def getListaServizi(self):
        return Servizio.query.all()

    def verificaProprietaAnnuncio(self, annuncio_id, utente_id):
        annuncio = AnnuncioStanza.query.get(annuncio_id)
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
            
        if annuncio.locatore_id != utente_id:
            raise ValueError("Azione non autorizzata. Non sei il proprietario di questo annuncio.")
            
        return annuncio

