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
        utente = Utente.cercaUtentePerEmail(email)
        if utente and utente.ruolo == 'studente':
            return utente
        return None

    @staticmethod
    def validaPassword(password):
        if len(password) < 8:
            return False
        if not re.search(r"\d", password):#verifico la presenza di una cifra numerica
            return False
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password): #verfico la presenza di un carattere speciale
            return False
        return True

    @staticmethod
    def login(email, password):
        utente = Utente.cercaUtentePerEmail(email)

        if not utente:
            raise ValueError("Credenziali errate.")
        
        if not check_password_hash(utente.password, password):
            raise ValueError("Credenziali errate.")

        if not utente.verificato:
            GestoreUtente.inviaEmailVerifica(email)
            raise ValueError("Il tuo account è in attesa di verifica. Ti abbiamo inviato una nuova email.") 

        return utente

    @staticmethod
    def registrazioneUtente(dati_form):

        email = dati_form.get('email')
        password = dati_form.get('password')
        ruolo = dati_form.get('ruolo')
        nome=dati_form.get('nome')
        cognome=dati_form.get('cognome')
        numTelefono=dati_form.get('numTelefono')

        if not nome or not cognome or not email or not ruolo:
            raise ValueError("Compila tutti i campi")

        # Controllo unicità email
        if Utente.cercaUtentePerEmail(email):
            raise ValueError("L'email inserita è già in uso.")

        # Controllo validità password
        if not GestoreUtente.validaPassword(password):
            raise ValueError("La password deve avere almeno 8 caratteri, un numero e un carattere speciale.")

        # Faccio l'hashing della password
        hashed_pw = generate_password_hash(password)

        if ruolo == 'studente':
            corso = dati_form.get('corso')
            facolta = dati_form.get('facolta')
            universita = dati_form.get('universita')

            if not corso or not facolta  or not universita:
                raise ValueError("Compila tutti i campi")

            nuovo_utente = Studente( nome=nome, cognome=cognome,email=email,numTelefono=numTelefono,password=hashed_pw,verificato=False, 
                                    corso=corso,facolta=facolta,universita=universita)
        elif ruolo == 'locatore':
            nuovo_utente = Locatore( nome=nome, cognome=cognome, email=email, numTelefono=numTelefono, password=hashed_pw, verificato=False)
        else:
            raise ValueError("Ruolo non valido.")

        db.session.add(nuovo_utente)
        db.session.commit()

        GestoreUtente.inviaEmailVerifica(email)
        
        return nuovo_utente
    
    @staticmethod
    def inviaEmailVerifica(email):
        token = GestoreUtente.generaTokenVerifica(email)
        link_verifica = url_for('gestione_utente.verify_email', token=token, _external=True)
        
        msg = Message(
            "Verifica il tuo account",
            recipients=[email]
        )
        msg.body = f"Grazie per esserti registrato!\n\nPer attivare il tuo account, clicca sul seguente link di conferma:\n{link_verifica}\n\nIl link rimarrà attivo per un'ora."
        
        mail.send(msg)
    
    @staticmethod
    def verificaEmail(token):
        try:
            email = GestoreUtente.confermaTokenVerifica(token)
        except:
            raise ValueError("Il link di attivazione è invalido o è scaduto")
        
        if not email:
            raise ValueError("Il link di attivazione è invalido o è scaduto")
        
        utente = Utente.cercaUtentePerEmail(email)
        
        if not utente:
            raise ValueError("Nessun account associato a questo indirizzo email")
        
        if utente.verificato:
            raise ValueError("Questo account risulta già verificato")
        
        utente.verificato = True
        db.session.commit()
        
    @staticmethod
    def generaTokenVerifica(email):
        #Inzializzo il serializer con la mia chiave privata
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        #Ritorno il token firmato contente la mia email
        return serializer.dumps(email, salt="email-verification-salt")

    @staticmethod
    def confermaTokenVerifica(token, expiration=3600):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            #prelevo il token verificando che non sia scaduto
            email = serializer.loads(token, salt="email-verification-salt", max_age=expiration)
            return email
        except (SignatureExpired, BadTimeSignature):
            return None
        
    @staticmethod
    def modificaProfilo(utente, dati_form):        
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


        nome = dati_form.get('nome', utente.nome)
        cognome = dati_form.get('cognome', utente.cognome)

        if not nome or not cognome:
            raise ValueError("Compila tutti i campi")


        # Aggiornamento dati anagrafici
        utente.nome = nome
        utente.cognome = cognome
        utente.numTelefono =  dati_form.get('numTelefono', utente.numTelefono)


        # Se l'istanza dell'utente è uno Studente, aggiorna anche le informazioni accademiche
        if utente.ruolo == 'studente':
            universita =dati_form.get('universita', utente.universita)
            facolta = dati_form.get('facolta', utente.facolta)
            corso = dati_form.get('corso', utente.corso)
            if not universita or not facolta or not corso:
                raise ValueError("Compila tutti i campi")


            utente.universita = universita
            utente.facolta = facolta
            utente.corso = corso

   
            
        db.session.commit()

    @staticmethod
    def eliminaProfilo(utente_id):
        utente = Utente.query.get(utente_id)
        if not utente:
            raise ValueError("Utente non trovato")
        
        db.session.delete(utente)
        db.session.commit()

    @staticmethod
    def generaNuovaPassword():
        caratteri = string.ascii_letters
        numeri = string.digits
        speciali = "!@#$%^&*(),.?\":{}|<>"
        # Genero almeno un numero e un carattere speciale 
        password_list = [
            random.choice(numeri),
            random.choice(speciali)
        ]
        
        # Riempo i restanti caratteri in modo casuale
        tutti_i_caratteri = caratteri + numeri + speciali
        password_list += [random.choice(tutti_i_caratteri) for _ in range(8)]
        
        # Mischio i caratteri per evitare schemi prevedibili
        random.shuffle(password_list)
        return "".join(password_list)
    
    @staticmethod
    def recuperaPassword(email):
        utente = Utente.cercaUtentePerEmail(email)
        if not utente:
            raise ValueError("Nessun account associato a questo indirizzo email.")
        
        #Genero la nuova password
        nuova_password = GestoreUtente.generaNuovaPassword()
        
        utente.password = generate_password_hash(nuova_password)
        #Invio l'email
        msg = Message("Recupero Password - UniAlloggi", recipients=[email])
        msg.body = f"Hai richiesto il recupero della password per il tuo account UniAlloggi.\n\nLa tua nuova password generata dal sistema è: {nuova_password}\n\nPuoi utilizzare questa password per effettuare il login. Ti consigliamo di modificarla successivamente dal tuo profilo."
        try:
            mail.send(msg)
            #Aggiorno la password cifrata nel db solo dopo l'invio della email
            db.session.commit()
        except Exception:
            #Se l'invio dell'eamil non va a buon fine riporto la sessione del database a quella iniziale e sollevo l'eccezione
            db.session.rollback() 
            raise ValueError("Impossibile inviare l'email di recupero password.")

    @staticmethod
    def visualizzaProfilo(utente_id):
        utente = Utente.query.get(utente_id)
        if not utente:
            raise ValueError("Utente non trovato")
        return utente
    