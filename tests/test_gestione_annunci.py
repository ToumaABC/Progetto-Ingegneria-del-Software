import unittest
from sqlalchemy import select,func
from io import BytesIO
from unittest.mock import patch
from app import  db
from app.GestioneFoto.models import FotoAnnuncio
from app.GestioneUtente.models import Locatore
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio
from werkzeug.security import generate_password_hash
from tests.base import BaseTestCase


class TestGestioneAnnunci(BaseTestCase):

    def setUp(self):
        super().setUp()

        # Utente Locatore di test
        pw_hash = generate_password_hash("Password123!")
        self.locatore = Locatore(
            nome="Mario",
            cognome="Rossi",
            email="locatore@test.com",
            password=pw_hash,
            ruolo='locatore',
            verificato=True
        )
        db.session.add(self.locatore)

        # Servizio di test
        self.servizio = Servizio(nome_servizio="WiFi")
        db.session.add(self.servizio)
        db.session.commit()

        # Login automatico
        self.login('locatore@test.com', 'Password123!')


    #@patch mi permette aggirare la chaiamta di GestoreFoto.salva_file_fisico senza caricare effettivamente il file
    @patch('app.GestioneFoto.gestore_foto.GestoreFoto.salva_file_fisico')
    def test_aggiungi_annuncio_valido(self, mock_salva_file):
        mock_salva_file.return_value = "uploads/annunci/fake.jpg"
        data = {
            'titolo': 'Stanza Valida',
            'indirizzo': 'Via Roma 1',
            'descrizione': 'Ottima stanza.',
            'costo': '300.0',
            'servizi': [str(self.servizio.id)],
            'foto': (BytesIO(b'dummy'), 'test.jpg') #Creo un file virtuale
        }
        response = self.client.post('/aggiungi_annuncio', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        annuncio = db.session.scalars(select(AnnuncioStanza)).first()
        self.assertIsNotNone(annuncio)
        self.assertEqual(annuncio.titolo, 'Stanza Valida')

    @patch('app.GestioneFoto.gestore_foto.GestoreFoto.salva_file_fisico')
    def test_aggiungi_annuncio_mancante_campi(self, mock_salva_file):
        # Aggiungo l'annuncio senza campo costo e indirizzo
        data = {
            'titolo': 'Stanza Errata',
            'descrizione': 'Mancano campi',
            'foto': (BytesIO(b'dummy'), 'test.jpg') 
        }
        response = self.client.post('/aggiungi_annuncio', data=data, content_type='multipart/form-data', follow_redirects=True)
        
        # Verifica che il gestore abbia sollevato il ValueError catturato dalla route e mostrato nel flash
        self.assertIn("compila tutti i campi obbligatori", response.data.decode('utf-8').lower())
        
        # Verifica che nessun annuncio sia stato creato
        numero_annunci = db.session.scalar(select(func.count()).select_from((AnnuncioStanza)))

        self.assertEqual(numero_annunci, 0)

    def test_modifica_annuncio_valido(self):
        annuncio = AnnuncioStanza(
            titolo="Da modificare",
            indirizzo="Via Vecchia 1",
            descrizione="Descrizione vecchia",
            costo=200.0,
            locatore_id=self.locatore.id
        )
        db.session.add(annuncio)
        db.session.flush()  # per avere annuncio.id prima del commit

        # Un annuncio reale ha  almeno una foto
        db.session.add(FotoAnnuncio(percorso_file="uploads/annunci/vecchia.jpg", annuncio_id=annuncio.id))
        db.session.commit()

        data = {
            'titolo': 'Stanza Modificata',
            'indirizzo': 'Via Nuova 2',
            'descrizione': 'Descrizione aggiornata.',
            'costo': '350.0',
            'servizi': [str(self.servizio.id)],
        }
        response = self.client.post(f'/modifica_annuncio/{annuncio.id}', data=data, content_type='multipart/form-data',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        annuncio_modificato = db.session.get(AnnuncioStanza, annuncio.id)
        self.assertEqual(annuncio_modificato.titolo, 'Stanza Modificata')
        self.assertEqual(annuncio_modificato.indirizzo, 'Via Nuova 2')
        self.assertEqual(annuncio_modificato.descrizione, 'Descrizione aggiornata.')
        self.assertEqual(annuncio_modificato.costo, 350.0)

    def test_modifica_annuncio_senza_foto_rimanenti_fallisce(self):
        annuncio = AnnuncioStanza(
            titolo="Da modificare", indirizzo="Via Vecchia 1",
            descrizione="Descrizione vecchia", costo=200.0,
            locatore_id=self.locatore.id
        )
        db.session.add(annuncio)
        db.session.flush()
        foto = FotoAnnuncio(percorso_file="uploads/annunci/unica.jpg", annuncio_id=annuncio.id)
        db.session.add(foto)
        db.session.commit()

        data = {
            'titolo': 'Stanza Modificata',
            'indirizzo': 'Via Nuova 2',
            'descrizione': 'Descrizione aggiornata.',
            'costo': '350.0',
            'servizi': [str(self.servizio.id)],
            'foto_da_eliminare': [str(foto.id_foto)],  # elimino l'unica foto, senza caricarne di nuove
        }
        response = self.client.post(f'/modifica_annuncio/{annuncio.id}', data=data, content_type='multipart/form-data',
                                    follow_redirects=True)

        self.assertIn("almeno una foto", response.data.decode('utf-8').lower())

        annuncio_invariato = db.session.get(AnnuncioStanza, annuncio.id)
        self.assertEqual(annuncio_invariato.titolo, 'Da modificare')
        self.assertEqual(len(annuncio_invariato.foto), 1)

    @patch('app.GestioneFoto.gestore_foto.GestoreFoto.elimina_file_fisico')
    def test_elimina_annuncio_valido(self, mock_elimina):
        annuncio = AnnuncioStanza(
            titolo="Da eliminare", indirizzo="Via Del Test",
            descrizione="Test", costo=250.0, locatore_id=self.locatore.id
        )
        db.session.add(annuncio)
        db.session.commit()

        response = self.client.post(f'/elimina_annuncio/{annuncio.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(db.session.get(AnnuncioStanza,annuncio.id))

    def test_elimina_annuncio_inesistente(self):
        # L'ID 999 non esiste nel DB.
        response = self.client.post('/elimina_annuncio/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("annuncio non trovato",response.data.decode("utf-8").lower())



if __name__ == '__main__':
    unittest.main()