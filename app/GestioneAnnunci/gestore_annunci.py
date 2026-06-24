import os
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, AnnuncioServizio, AnnuncioSalvato
from app.GestioneFoto.models import FotoAnnuncio
from app.GestioneFoto.gestore_foto import GestoreFoto


class GestoreAnnunci:

    @staticmethod
    def aggiungiAnnuncio(dati_form, file_foto, locatore_id):
        """Metodo per la creazione di un nuovo annuncio (RF-7)."""
        titolo = dati_form.get('titolo')
        indirizzo = dati_form.get('indirizzo')
        descrizione = dati_form.get('descrizione')
        costo = dati_form.get('costo')

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
        #Faccio il flush per ottenere l'id dell'annuncio
        db.session.flush() 

        # Gestione Servizi
        servizi_selezionati = dati_form.getlist('servizi')
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=nuovo_annuncio.id, servizio_id=servizio.id)
                db.session.add(annuncio_servizio)

        # Gestione Foto
        if not file_foto or file_foto[0].filename == '':
             raise ValueError("È richiesta almeno una foto per l'annuncio.")


        for file in file_foto:
            percorso = GestoreFoto.salva_file_fisico(file, 'annunci', 'annuncio', nuovo_annuncio.id)
            if percorso:
                nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=nuovo_annuncio.id)
                db.session.add(nuova_foto)

        db.session.commit()
        return nuovo_annuncio

    @staticmethod
    def modificaAnnuncio(annuncio, dati_form, file_foto=None, foto_da_eliminare=None):
        """Metodo per la modifica dei dati di un annuncio e delle sue foto."""
        
        # 1. Aggiornamento dei campi testuali
        annuncio.titolo = dati_form.get('titolo', annuncio.titolo)
        annuncio.indirizzo = dati_form.get('indirizzo', annuncio.indirizzo)
        annuncio.descrizione = dati_form.get('descrizione', annuncio.descrizione)
        
        costo = dati_form.get('costo')
        if costo:
            annuncio.costo = float(costo)

        # Eliminazione delle foto selezionate
        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto_check = FotoAnnuncio.query.get(foto_id)
                if foto_check and foto_check.annuncio_id == annuncio.id:
                    GestoreFoto.elimina_foto_db(foto_check)

        # 3. Aggiunta delle nuove foto
        if file_foto:
            for file in file_foto:
                percorso = GestoreFoto.salva_file_fisico(file, sotto_cartella='annunci', prefisso_nome='annuncio', id_entita=annuncio.id)
                if percorso:
                    nuova_foto = FotoAnnuncio(percorso_file=percorso, annuncio_id=annuncio.id)
                    db.session.add(nuova_foto)

        # 4. Aggiornamento dei servizi: rimuovo i collegamenti esistenti e ricreo quelli selezionati
        servizi_selezionati = dati_form.getlist('servizi')
        AnnuncioServizio.query.filter_by(annuncio_id=annuncio.id).delete()
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                annuncio_servizio = AnnuncioServizio(annuncio_id=annuncio.id, servizio_id=servizio.id)
                db.session.add(annuncio_servizio)

        db.session.commit()

    @staticmethod
    def eliminaAnnuncio(annuncio):
        for foto in annuncio.foto:
            GestoreFoto.elimina_file_fisico(foto.percorso_file)
        db.session.delete(annuncio)
        db.session.commit()

    @staticmethod
    def cambiaVisibilita(annuncio):
        """Oscura o rende visibile un annuncio (RF-14)."""
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
            # Per ogni servizio selezionato, obblighiamo l'annuncio a possederlo 
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
        salvataggio_esistente = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if salvataggio_esistente:
            return False
        nuovo_salvataggio = AnnuncioSalvato(studente_id=studente_id, annuncio_id=annuncio_id)
        db.session.add(nuovo_salvataggio)
        db.session.commit()
        return True

    @staticmethod
    def eliminaAnnuncioSalvato(studente_id, annuncio_id):
        salvataggio = AnnuncioSalvato.query.filter_by(studente_id=studente_id, annuncio_id=annuncio_id).first()
        if salvataggio:
            db.session.delete(salvataggio)
            db.session.commit()
            return True
        return False

    @staticmethod
    def getAnnunciSalvati(studente_id):
        salvataggi = AnnuncioSalvato.query.filter_by(studente_id=studente_id).all()
        return [salvataggio.annuncio for salvataggio in salvataggi]
