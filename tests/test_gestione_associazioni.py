import unittest
from app import create_app, db
from app.GestioneUtente.models import Locatore, Studente
from app.GestioneAnnunci.models import AnnuncioStanza
from app.GestioneStanza.models import AssociazioneStudenteStanza
from werkzeug.security import generate_password_hash

class TestGestioneAssociazioni(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.drop_all()
        db.create_all()

        pw_hash = generate_password_hash("Password123!")
        
        # Crea e salva un locatore e uno studente
        self.locatore = Locatore(
            nome="Mario", cognome="Rossi", email="locatore@test.com",
            password=pw_hash, ruolo="locatore", verificato=True
        )
        self.studente = Studente(
            nome="Anna", cognome="Verdi", email="anna@studenti.com",
            password=pw_hash, ruolo="studente", verificato=True
        )
        db.session.add(self.locatore)
        db.session.add(self.studente)
        db.session.commit()

        # Crea e salva un annuncio legato al locatore
        self.annuncio = AnnuncioStanza(
            titolo="Stanza per test associazione", indirizzo="Via Università",
            descrizione="Test", costo=250.0, locatore_id=self.locatore.id
        )
        db.session.add(self.annuncio)
        db.session.commit()

        # Login automatico come Locatore
        self.client.post('/login', data={'email': 'locatore@test.com', 'password': 'Password123!'}, follow_redirects=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_associa_studente_valido(self):
        # Il locatore associa lo studente all'annuncio
        response = self.client.post(f'/annuncio/{self.annuncio.id}/associa', data={
            'email_studente': 'anna@studenti.com'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        
        # Verifica nel database
        associazione = AssociazioneStudenteStanza.query.filter_by(
            annuncio_id=self.annuncio.id, studente_id=self.studente.id
        ).first()
        self.assertIsNotNone(associazione)
        self.assertTrue(associazione.attiva)

    def test_associa_studente_email_errata(self):
        # Tenta di associare un'email che non appartiene a nessuno studente
        response = self.client.post(f'/annuncio/{self.annuncio.id}/associa', data={
            'email_studente': 'inesistente@email.com'
        }, follow_redirects=True)

        # Controlla il messaggio di flash generato dal ValueError nel gestore
        self.assertIn("nessuno studente trovato con questa email", response.data.decode('utf-8').lower())
        self.assertEqual(AssociazioneStudenteStanza.query.count(), 0)

    def test_associa_studente_gia_associato(self):
        # 1. Creiamo un'associazione già attiva manualmente
        associazione = AssociazioneStudenteStanza(
            annuncio_id=self.annuncio.id, studente_id=self.studente.id, attiva=True
        )
        db.session.add(associazione)
        db.session.commit()

        # 2. Proviamo ad associarlo nuovamente
        response = self.client.post(f'/annuncio/{self.annuncio.id}/associa', data={
            'email_studente': 'anna@studenti.com'
        }, follow_redirects=True)

        self.assertIn("già associato", response.data.decode('utf-8').lower())
        # Ci aspettiamo che l'associazione nel DB rimanga 1
        self.assertEqual(AssociazioneStudenteStanza.query.count(), 1)

    def test_annulla_associazione(self):
        # Precondizione: studente associato
        associazione = AssociazioneStudenteStanza(
            annuncio_id=self.annuncio.id, studente_id=self.studente.id, attiva=True
        )
        db.session.add(associazione)
        db.session.commit()

        # Locatore annulla l'associazione
        response = self.client.post(f'/annuncio/{self.annuncio.id}/annulla_associazione/{self.studente.id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Verifichiamo che l'associazione non sia stata eliminata ma solo disattivata
        associazione_disattivata = AssociazioneStudenteStanza.query.get(associazione.id)
        self.assertIsNotNone(associazione_disattivata)
        self.assertFalse(associazione_disattivata.attiva)

if __name__ == '__main__':
    unittest.main()