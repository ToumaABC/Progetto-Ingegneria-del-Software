import unittest
from app import create_app, db
from app.GestioneUtente.models import Utente,Studente
from werkzeug.security import generate_password_hash


class TestGestioneUtente(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.drop_all()
        db.create_all()

        password_hash = generate_password_hash("Password123!")
        utente_test = Studente(
            nome="Mario", 
            cognome="Rossi", 
            email="mario.rossi@email.com", 
            password=password_hash, 
            ruolo="studente",
            verificato=True 
        )
        db.session.add(utente_test)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_registrazione_valida(self):
        # Simula l'invio del form di registrazione
        response = self.client.post('/register', data={
            'nome': 'Luigi',
            'cognome': 'Verdi',
            'email': 'luigi.verdi@email.com',
            'password': 'PasswordSicura456!',
            'ruolo': 'locatore'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verifica che l'utente sia stato effettivamente salvato nel database
        nuovo_utente = Utente.query.filter_by(email='luigi.verdi@email.com').first()
        self.assertIsNotNone(nuovo_utente)
        self.assertEqual(nuovo_utente.nome, 'Luigi')

    def test_registrazione_email_duplicata(self):
        # Tenta di registrare un utente con un'email già presente (mario.rossi@email.com)
        response = self.client.post('/register', data={
            'nome': 'Nuovo',
            'cognome': 'Utente',
            'email': 'mario.rossi@email.com', 
            'password': 'AltraPassword123!',
            'ruolo': 'studente'
        }, follow_redirects=True)
        
        self.assertIn("&#39;email inserita è già in uso.".encode('utf-8'), response.data.lower())
        
        # Verifica che gli utenti nel database siano rimasti 1
        utenti_totali = Utente.query.count()
        self.assertEqual(utenti_totali, 1)

    # --- TEST LOGIN ---

    def test_login_valido(self):
        # Simula l'invio del form di login con credenziali corrette
        response = self.client.post('/login', data={
            'email': 'mario.rossi@email.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logout', response.data.lower()) 

    def test_login_password_errata(self):
        # Simula il login con password sbagliata
        response = self.client.post('/login', data={
            'email': 'mario.rossi@email.com',
            'password': 'PasswordSbagliata!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Verifica che venga mostrato il messaggio di errore
        self.assertIn(b'credenziali errate', response.data.lower())

    def test_login_utente_inesistente(self):
        # Simula il login con una mail non registrata
        response = self.client.post('/login', data={
            'email': 'fantasma@email.com',
            'password': 'Password123!'
        }, follow_redirects=True)
        
        # Verifica che l'accesso sia negato
        self.assertIn(b'credenziali errate', response.data.lower())

if __name__ == '__main__':
    unittest.main()