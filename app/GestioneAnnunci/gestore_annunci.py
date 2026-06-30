import os
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, AnnuncioServizio, AnnuncioSalvato
from app.GestioneFoto.models import FotoAnnuncio
from app.GestioneFoto.gestore_foto import GestoreFoto


class GestoreAnnunci:

    @staticmethod
    def aggiungiAnnuncio(dati, servizi, file_foto, locatore_id):
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
        db.session.add(nuovo_annuncio)
        #Faccio il flush per ottenere l"id dell"annuncio
        db.session.flush() 

        # Gestione Servizi
        servizi_selezionati = servizi
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=nuovo_annuncio.id, servizio_id=servizio.id)
                db.session.add(annuncio_servizio)

        # Gestione Foto
        if not file_foto or file_foto[0].filename == "":
             raise ValueError("È richiesta almeno una foto per l'annuncio.")


        for file in file_foto:
            percorso = GestoreFoto.salva_file_fisico(file, "annunci", "annuncio", nuovo_annuncio.id)
            if percorso:
                nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=nuovo_annuncio.id)
                db.session.add(nuova_foto)

        db.session.commit()
        return nuovo_annuncio

    @staticmethod
    def modificaAnnuncio(annuncio, servizi, dati, file_foto=None, foto_da_eliminare=None):

        # 1. Aggiornamento dei campi testuali
        annuncio.titolo = dati.get("titolo", annuncio.titolo)
        annuncio.indirizzo = dati.get("indirizzo", annuncio.indirizzo)
        annuncio.descrizione = dati.get("descrizione", annuncio.descrizione)
        
        costo = dati.get("costo")
        if costo:
            annuncio.costo = float(costo)

        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = FotoAnnuncio.query.get(foto_id)
                if foto_check and foto_check.annuncio_id == annuncio.id:
                    GestoreFoto.elimina_foto_db(foto_check)

        if file_foto:
            for file in file_foto:
                percorso = GestoreFoto.salva_file_fisico(file, sotto_cartella="annunci", prefisso_nome="annuncio", id_entita=annuncio.id)
                if percorso:
                    nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=annuncio.id)
                    db.session.add(nuova_foto)

        servizi_selezionati = servizi
        AnnuncioServizio.query.filter_by(annuncio_id=annuncio.id).delete()
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=annuncio.id, servizio_id=servizio.id)
                db.session.add(annuncio_servizio)

        db.session.commit()

    @staticmethod
    def eliminaAnnuncio(annuncio_id,user_id):
        annuncio = GestoreAnnunci.verifica_proprieta_annuncio(annuncio_id, user_id)
        for foto in annuncio.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)
        db.session.delete(annuncio)
        db.session.commit()

    @staticmethod
    def cambiaVisibilita(annuncio):
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
        annuncio.visibile = not annuncio.visibile
        db.session.commit()
        return annuncio.visibile

    @staticmethod
    def ricerca_annunci(query_testo=None, prezzo_max=None, servizi_selezionati=None):

        annunci = AnnuncioStanza.query.filter_by(visibile=True)

        # Esecuzione flusso principale (Ricerca)
        if query_testo:
            search = f"%{query_testo}%"
            annunci = annunci.filter(
                db.or_(
                    AnnuncioStanza.indirizzo.ilike(search),
                    AnnuncioStanza.titolo.ilike(search),
                    AnnuncioStanza.descrizione.ilike(search)
                )
            )

        # Punto di estensione se ci sono filtri appllico i giltri
        if prezzo_max or servizi_selezionati:
            annunci = GestoreAnnunci.filtra_annunci(annunci, prezzo_max,servizi_selezionati)
            
        return annunci.all()

    @staticmethod
    def filtra_annunci(l_annunci, prezzo_max=None, servizi_selezionati=None):
        try:
            prezzo = float(prezzo_max)
            l_annunci = l_annunci.filter(AnnuncioStanza.costo <= prezzo)
        except ValueError:
            pass # Se il valore non è numerico, restituisce la query inalterata
        
        if servizi_selezionati:
            # Per ogni servizio selezionato, obblighiamo l"annuncio a possederlo 
            print("Ciao")

            for serv_id in servizi_selezionati:
                try:
                    id_serv = int(serv_id)
                    subquery = db.session.query(AnnuncioServizio.annuncio_id).filter(AnnuncioServizio.servizio_id == id_serv)
                    l_annunci = l_annunci.filter(AnnuncioStanza.id.in_(subquery))
                except ValueError:
                    pass
                
        return l_annunci
    
    @staticmethod
    def salvaAnnuncio(studente_id, annuncio_id):
        if not AnnuncioStanza.query.get(annuncio_id) :
            raise ValueError("Annuncio non trovato.")
        salvataggio_esistente = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if salvataggio_esistente:
            raise ValueError("Hai già salvato questo annuncio.")
        nuovo_salvataggio = AnnuncioSalvato(studente_id=studente_id, annuncio_id=annuncio_id)
        db.session.add(nuovo_salvataggio)
        db.session.commit()

    @staticmethod
    def eliminaAnnuncioSalvato(studente_id, annuncio_id):
        salvataggio = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if not salvataggio:
            raise ValueError("Non puoi rimuovere un annuncio non salvato ")
        db.session.delete(salvataggio)
        db.session.commit()
            


    @staticmethod
    def get_lista_servizi():
        return Servizio.query.all()
    
    @staticmethod
    def verifica_proprieta_annuncio(annuncio_id, utente_id):
        annuncio = AnnuncioStanza.query.get(annuncio_id)
        if not annuncio:
            raise ValueError("Annuncio non trovato.")
            
        if annuncio.locatore_id != utente_id:
            raise ValueError("Azione non autorizzata. Non sei il proprietario di questo annuncio.")
            
        return annuncio
    