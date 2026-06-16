import os
from flask import current_app
from werkzeug.utils import secure_filename
from app import db
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, FotoAnnuncio

class GestoreAnnunci:

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in GestoreAnnunci.ALLOWED_EXTENSIONS

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
        db.session.flush() # Per ottenere l'ID dell'annuncio appena creato

        # Gestione Servizi
        servizi_selezionati = dati_form.getlist('servizi')
        for serv_id in servizi_selezionati:
            servizio = Servizio.query.get(serv_id)
            if servizio:
                nuovo_annuncio.servizi_collegati.append(servizio)

        # Gestione Foto
        if not file_foto or file_foto[0].filename == '':
             raise ValueError("È richiesta almeno una foto per l'annuncio.")

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'annunci')
        os.makedirs(upload_folder, exist_ok=True)

        for file in file_foto:
            if file and GestoreAnnunci.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(upload_folder, filename)
                
                file.save(filepath)
                
                nuova_foto = FotoAnnuncio(percorso_file=f"uploads/annunci/{filename}", annuncio_id=nuovo_annuncio.id)
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

        # 2. Eliminazione delle foto selezionate
        if foto_da_eliminare:
            for foto_id in foto_da_eliminare:
                foto = FotoAnnuncio.query.get(foto_id)
                # Controllo di sicurezza: verifichiamo che la foto appartenga a questo annuncio
                if foto and foto.annuncio_id == annuncio.id:
                    # Rimuoviamo il file fisico dal server
                    percorso_fisico = os.path.join(current_app.root_path, 'static', foto.percorso_file)
                    if os.path.exists(percorso_fisico):
                        try:
                            os.remove(percorso_fisico)
                        except Exception as e:
                            print(f"Errore durante l'eliminazione del file: {e}")
                    
                    # Rimuoviamo il record dal database
                    db.session.delete(foto)

        # 3. Aggiunta delle nuove foto
        if file_foto:
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'annunci')
            os.makedirs(upload_folder, exist_ok=True)

            for file in file_foto:
                # Se il file è valido e non è vuoto
                if file and file.filename != '' and GestoreAnnunci.allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_folder, filename)
                    
                    file.save(filepath)
                    
                    nuova_foto = FotoAnnuncio(percorso_file=f"uploads/annunci/{filename}", annuncio_id=annuncio.id)
                    db.session.add(nuova_foto)

        db.session.commit()

    @staticmethod
    def eliminaAnnuncio(annuncio):
        """Rimuove permanentemente un annuncio dal database (RF-10)."""
        # Grazie alla relazione cascade nel model, elimina anche le foto associate
        db.session.delete(annuncio)
        db.session.commit()

    @staticmethod
    def cambiaVisibilita(annuncio):
        """Oscura o rende visibile un annuncio (RF-14)."""
        annuncio.visibile = not annuncio.visibile
        db.session.commit()
        return annuncio.visibile