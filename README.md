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

Segui questi passaggi per scaricare ed eseguire il sistema sul tuo computer.

### Prerequisiti
* Python 3.8 o superiore installato sul sistema.
* Git installato (opzionale, ma consigliato per clonare la repository).

### 1. Clona il repository
Apri il terminale e clona il progetto in locale:
` ` `bash
git clone https://github.com/ToumaABC/Progetto-Ingegneria-del-Software.git
cd Progetto-Ingegneria-del-Software
` ` `
*(Ricordati di sostituire il link con l'URL effettivo del tuo repository GitHub)*

### 2. Crea un ambiente virtuale (Consigliato)
È buona norma utilizzare un ambiente virtuale per isolare le dipendenze del progetto:
* **Su Windows:**
  ` ` `bash
  python -m venv venv
  venv\Scripts\activate
  ` ` `
* **Su macOS/Linux:**
  ` ` `bash
  python3 -m venv venv
  source venv/bin/activate
  ` ` `

### 3. Installa le dipendenze
Con l'ambiente virtuale attivo, installa le librerie necessarie (come Flask) elencate nel file `requirements.txt`:
` ` `bash
pip install -r requirements.txt
` ` `

### 4. Avvia l'applicazione
Esegui il file principale dell'applicazione:
` ` `bash
python app.py
` ` `

### 5. Apri l'applicazione
Una volta avviato il server, apri il tuo browser web e vai al seguente indirizzo per visualizzare la Home Page:
👉 **http://127.0.0.1:5000/**

---

## 👥 Autori
* Tommaso Britto
* Yi Qiao Hu
* Alex Eliaruny

*Progetto realizzato per il corso di Ingegneria del Software - Università Politecnica delle Marche
