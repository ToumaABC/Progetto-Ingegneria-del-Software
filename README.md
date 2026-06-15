# Sistema per la Gestione e Ricerca di alloggi universitari 🏠🎓

**Piattaforma software per semplificare e rendere più sicuro il mercato degli affitti accademici.**

Questo sistema è una piattaforma software sviluppata in Python dedicata esclusivamente alla gestione e alla ricerca di alloggi per studenti universitari. L'obiettivo principale è offrire strumenti completi e dedicati sia per i locatori che per gli studenti.

## 🚀 Funzionalità Principali

* **Gestione Utenti:** Registrazione, login e profilazione distinta tra Studenti e Locatori.
* **Gestione Annunci:** I locatori possono creare, modificare, nascondere o eliminare annunci completi di foto e dettagli sui servizi.
* **Ricerca e Filtri:** Gli studenti possono cercare alloggi tramite parole chiave, filtrare i risultati per servizi e salvare gli annunci preferiti.
* **Gestione Inquilini:** Associazione e dissociazione ufficiale degli studenti alle stanze da parte dei locatori.
* **Ticketing:** Sistema di segnalazione guasti integrato per comunicazioni dirette tra inquilini e locatori.
* **Recensioni Verificate:** Sistema di feedback accessibile solo agli studenti associati a un alloggio, per garantire recensioni reali al 100%.

## 🛠️ Architettura e Tecnologie (Stack)

* **Linguaggio:** Python 3.x
* **Framework Web:** Flask (Backend/API)
* **Database:** SQLite (Relazionale)
* **Architettura:** Model-View-Controller (MVC) tramite classi `Gestore` (Manager pattern).

## ⚙️ Come avviare il progetto (Setup Locale)
Certamente! Un buon file `README.md` è fondamentale per presentare il tuo progetto su GitHub e permettere ai docenti o ad altri sviluppatori di testarlo senza problemi.

Ecco un template completo e professionale per il tuo **README**, strutturato appositamente per l'architettura Flask che abbiamo costruito insieme.

Puoi copiare questo testo e incollarlo direttamente in un file chiamato `README.md` nella root del tuo progetto (accanto a `run.py`).


## ⚙️ Configurazione e Installazione

Segui questi passaggi per configurare l'ambiente di sviluppo e avviare l'applicazione sul tuo server locale.

### 1. Prerequisiti
Assicurati di avere **Python 3.8+** installato sul tuo sistema. Puoi verificarlo lanciando:
```bash
python --version

```

### 2. Clona il Repository

Scarica il progetto da GitHub e spostati nella cartella radice:

```bash
git clone [https://github.com/ToumaABC/Progetto-Ingegneria-del-Software.git]
cd Progetto-Ingegneria-del-Software

```

### 3. Crea e Attiva un Ambiente Virtuale (VENV)

È fortemente consigliato isolare le dipendenze del progetto.

* **Su Windows:**
```bash
python -m venv venv
venv\Scripts\activate

```


* **Su macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate

```



### 4. Installa le Dipendenze

Con l'ambiente virtuale attivo, installa i pacchetti necessari tramite `requirements.txt`:

```bash
pip install -r requirements.txt

```


### 5. Configura le Variabili d'Ambiente (`.env`)

Nella cartella principale (dove si trova `run.py`), crea un file denominato esattamente **`.env`** (senza estensioni prima del punto) e inserisci le configurazioni del server email e del database:

```ini
# Sicurezza Flask
SECRET_KEY=inserisci_una_chiave_segreta_molto_lunga_e_casuale
DATABASE_URL=sqlite:///database.sqlite

# Configurazione SMTP (Es. Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=la_tua_email@gmail.com
MAIL_PASSWORD=la_tua_password_per_le_app_di_gmail
MAIL_DEFAULT_SENDER=noreply@unialloggi.it

```

> **Nota per Gmail:** Se usi Gmail, al posto della password normale devi generare una "Password per le app" dalle impostazioni di sicurezza dell'account Google (l'autenticazione a due fattori deve essere attiva).

### 6. Avvia l'Applicazione

Il database SQLite (`database.sqlite`) verrà creato automaticamente al primo avvio. Per far partire il server locale, esegui:

```bash
python run.py

```

Il terminale ti mostrerà un indirizzo (solitamente `http://127.0.0.1:5000`). Apri questo link nel browser per navigare nella piattaforma!

---

## 📂 Struttura del Progetto

L'architettura del software rispecchia un design pattern orientato agli oggetti e basato su **package logici (Blueprints)**, aderente alla documentazione UML prodotta in fase di analisi.

```text
UniAlloggi/
│
├── app/                           # Applicazione core
│   ├── __init__.py                # App Factory & Inizializzazione moduli
│   │
│   ├── GestioneUtente/            # Package Logico: Gestione Account
│   │   ├── __init__.py            # Configurazione Blueprint
│   │   ├── models.py              # Entità (Utente, Studente, Locatore)
│   │   ├── gestore_utente.py      # Business Logic (Validazioni, Token, DB)
│   │   └── routes.py              # Controller / Endpoints HTTP
│   │
│   └── templates/                 # Livello di Presentazione (Frontend)
│       ├── base.html              # Layout principale (Bootstrap)
│       ├── login.html
│       ├── register.html
│       └── ...
│
├── .env                           # File nascosto per variabili di sistema sensibili
├── requirements.txt               # Lista delle dipendenze di sistema
└── run.py                         # Entry point per eseguire il server

```

## 👨‍💻 Autori

* **Tommaso Britto**
* **Yi Qiao Hu**
* **Alex Eliaruny**

Corso di Laurea in Ingegneria Informatica e dell'Automazione - Università Politecnica delle Marche.


