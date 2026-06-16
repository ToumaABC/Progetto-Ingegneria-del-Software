from flask import current_app, url_for
import string
import random
from flask_mail import Message
from app import db,mail
from app.GestioneUtente.models import Utente, Studente, Locatore
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
import re

class GestoreUtente:
    
    @staticmethod
    def cercaStudentePerEmail(email):
        """Cerca un utente tramite email."""
        utente = Utente.query.filter_by(email=email).first()
        if utente and utente.ruolo == 'studente':
            return utente
        return None

    @staticmethod
    def validaPassword(password):
        if len(password) < 8:
            return False
        if not re.search(r"\d", password):#verifico la presenza di un carettere maiuscolo
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password): #verfico la presenza di un carattere speciale
            return False
        return True

    @staticmethod
    def validaCredenziali(email, password):
        """Verifica email e password per il login."""
        utente = Utente.query.filter_by(email=email).first()

        if utente and check_password_hash(utente.password, password):
            return utente
        return None

    @staticmethod
    def registrazioneUtente(dati_form):

        """Metodo principale per la registrazione (Sequence Diagram 4.2.2)."""
        email = dati_form.get('email')
        password = dati_form.get('password')
        ruolo = dati_form.get('ruolo')

        # Controllo unicità email
        if Utente.query.filter_by(email=email).first():
            raise ValueError("L'email inserita è già in uso.")

        # Controllo validità password
        if not GestoreUtente.validaPassword(password):
            raise ValueError("La password deve avere almeno 8 caratteri, un numero e un carattere speciale.")

        # Hashing
        hashed_pw = generate_password_hash(password)

        if ruolo == 'studente':
            nuovo_utente = Studente(
                nome=dati_form.get('nome'),
                cognome=dati_form.get('cognome'),
                email=email,
                numTelefono=dati_form.get('numTelefono'),
                password=hashed_pw,
                verificato=False, 
                corso=dati_form.get('corso'),
                facolta=dati_form.get('facolta'),
                universita=dati_form.get('universita')
            )
        elif ruolo == 'locatore':
            nuovo_utente = Locatore(
                nome=dati_form.get('nome'),
                cognome=dati_form.get('cognome'),
                email=email,
                numTelefono=dati_form.get('numTelefono'),
                password=hashed_pw,
                verificato=False
            )
        else:
            raise ValueError("Ruolo non valido.")

        db.session.add(nuovo_utente)
        db.session.commit()

        GestoreUtente.inviaEmailVerifica(email)
        
        return nuovo_utente
    
    @staticmethod
    def inviaEmailVerifica(email):
        """Metodo previsto dal diagramma delle classi: + inviaEmail(String): void"""
        token = GestoreUtente.generaTokenVerifica(email)
        link_verifica = url_for('gestione_utente.verify_email', token=token, _external=True)
        
        msg = Message(
            "Verifica il tuo account - UniAlloggi",
            recipients=[email]
        )
        msg.body = f"Grazie per esserti registrato su UniAlloggi!\n\nPer attivare il tuo account, clicca sul seguente link di conferma:\n{link_verifica}\n\nIl link rimarrà attivo per un'ora."
        
        try:
            mail.send(msg)
        except Exception as e:
            # Fallback di debug se i dati SMTP nel file .env non sono ancora configurati/corretti
            print(f"\n[DEBUG] Errore SMTP nell'invio reale: {e}")
            print(f"[DEBUG] Generazione link di verifica simulato:\n--> {link_verifica}\n")


    @staticmethod
    def generaTokenVerifica(email):
        """Genera un token crittografico temporizzato basato sull'email."""
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(email, salt="email-verification-salt")

    @staticmethod
    def confermaTokenVerifica(token, expiration=3600):
        """Valida il token. Scade automaticamente dopo 1 ora (3600 secondi)."""
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            email = serializer.loads(token, salt="email-verification-salt", max_age=expiration)
            return email
        except (SignatureExpired, BadTimeSignature):
            return None
        

    @staticmethod
    def modificaProfilo(utente, dati_form):
        """Aggiorna i campi anagrafici, la password e gestisce dinamicamente i campi polimorfici."""
        
        # Gestione Modifica Password
        vecchia_password = dati_form.get('vecchia_password')
        nuova_password = dati_form.get('nuova_password')
        
        if vecchia_password and nuova_password:
            # Verifica che la vecchia password sia corretta
            if not check_password_hash(utente.password, vecchia_password):
                raise ValueError("La vecchia password non è corretta.")
            
            # Valida la nuova password usando i vincoli esistenti
            if not GestoreUtente.validaPassword(nuova_password):
                raise ValueError("La nuova password deve avere almeno 8 caratteri, un numero e un carattere speciale.")
            
            # Genera il nuovo hash e aggiorna
            utente.password = generate_password_hash(nuova_password)

        # Aggiornamento dati anagrafici
        utente.nome = dati_form.get('nome', utente.nome)
        utente.cognome = dati_form.get('cognome', utente.cognome)
        utente.numTelefono = dati_form.get('numTelefono', utente.numTelefono)
        
        # Se l'istanza dell'utente è uno Studente, aggiorna anche le informazioni accademiche
        if utente.ruolo == 'studente':
            utente.universita = dati_form.get('universita', utente.universita)
            utente.facolta = dati_form.get('facolta', utente.facolta)
            utente.corso = dati_form.get('corso', utente.corso)
            
        db.session.commit()

    @staticmethod
    def eliminaProfilo(utente):
        """Rimuove permanentemente l'account dal database SQLite."""
        db.session.delete(utente)
        db.session.commit()


    @staticmethod
    def generaNuovaPassword():
        """Genera una password casuale di 10 caratteri che rispetta i vincoli RNF-3."""
        caratteri = string.ascii_letters
        numeri = string.digits
        speciali = "!@#$%^&*(),.?\":{}|<>"

        # Garantiamo almeno un numero e un carattere speciale (RNF-3)
        password_list = [
            random.choice(numeri),
            random.choice(speciali)
        ]
        
        # Riempi i restanti 8 caratteri in modo casuale
        tutti_i_caratteri = caratteri + numeri + speciali
        password_list += [random.choice(tutti_i_caratteri) for _ in range(8)]
        
        # Mischia i caratteri per evitare schemi prevedibili
        random.shuffle(password_list)
        return "".join(password_list)
    
    @staticmethod
    def recuperaPassword(email):
        """
        Caso d'Uso 6: Recupero Password.
        Verifica l'esistenza dell'email, genera una nuova password, la aggiorna e la invia.
        """
        utente = Utente.query.filter_by(email=email).first()
        if not utente:
            raise ValueError("Nessun account associato a questo indirizzo email.")
        
        # 4. Il sistema genera la nuova password
        nuova_password = GestoreUtente.generaNuovaPassword()
        
        # Aggiorna il database con l'hash della nuova password
        utente.password = generate_password_hash(nuova_password)
        db.session.commit()
        
        # 5. Il sistema invia la nuova password all'Utente tramite email
        msg = Message("Recupero Password - UniAlloggi", recipients=[email])
        msg.body = f"Hai richiesto il recupero della password per il tuo account UniAlloggi.\n\nLa tua nuova password generata dal sistema è: {nuova_password}\n\nPuoi utilizzare questa password per effettuare il login. Ti consigliamo di modificarla successivamente dal tuo profilo."
        
        try:
            mail.send(msg)
        except Exception:
            # Fallback per debug se il server SMTP non è ancora attivo
            print(f"\n[DEBUG] Nuova password generata per {email}: {nuova_password}\n")