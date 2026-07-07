import unittest
from sqlalchemy import select,func
from io import BytesIO
from unittest.mock import patch
from app import create_app, db
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