from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from app.GestioneUtente import gestione_utente_bp
from app.GestioneUtente.gestore_utente import GestoreUtente
from functools import wraps
from app import db
from app.GestioneUtente.models import Utente



@gestione_utente_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_utente.profilo'))
    

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        utente = GestoreUtente.validaCredenziali(email, password)
        if utente:
            if not utente.verificato:
                flash('Accesso negato: il tuo account è in attesa di verifica. Controlla la tua email.', 'warning')
            
            else:
                login_user(utente)
                return redirect(url_for('gestione_annunci.index'))
        else:
            flash('Credenziali errate. Riprova.', 'danger')
            
    return render_template('gestione_utente/login.html')


@gestione_utente_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_utente.profilo'))
    if request.method == 'POST':
        try:
            GestoreUtente.registrazioneUtente(request.form)
            flash('Registrazione completata! Controlla la tua email per verificare l\'account.', 'success')
            return redirect(url_for('gestione_utente.login'))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('gestione_utente/register.html')


@gestione_utente_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout effettuato con successo.', 'info')
    return redirect(url_for('gestione_utente.login'))

@gestione_utente_bp.route('/profilo', methods=['GET'])
@login_required
def profilo():
    """
    RF-4 / Caso d'uso 4: Visualizza profilo.
    Mostra i dati dell'utente corrente e adatta la vista se l'attore è uno Studente.
    """
    # Passiamo l'utente corrente (current_user) al template
    return render_template('gestione_utente/profilo.html', utente=current_user)


@gestione_utente_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    """Transizione di stato del diagramma AccountUtente da 'In attesa di verifica' a 'Verificato'"""
    email = GestoreUtente.confermaTokenVerifica(token)
    if email:
        utente = Utente.query.filter_by(email=email).first()
        if utente:
            if utente.verificato:
                flash('Questo account risulta già verificato.', 'info')
            else:
                # Transizione di stato nel DB SQLite
                utente.verificato = True
                db.session.commit()
                flash('Account verificato con successo! Benvenuto in UniAlloggi, ora puoi effettuare il login.', 'success')
            return redirect(url_for('gestione_utente.login'))
            
    flash('Il link di attivazione è invalido o è scaduto.', 'danger')
    return redirect(url_for('gestione_utente.register'))


@gestione_utente_bp.route('/profilo/modifica', methods=['GET', 'POST'])
@login_required
def modifica_profilo():
    if request.method == 'POST':
        try:
            GestoreUtente.modificaProfilo(current_user, request.form)
            flash('Profilo aggiornato correttamente.', 'success')
            return redirect(url_for('gestione_utente.profilo'))
        except ValueError as e:
            # Mostra l'errore (es. "La vecchia password non è corretta")
            flash(str(e), 'danger')
        
    return render_template('gestione_utente/modifica_profilo.html', utente=current_user)


@gestione_utente_bp.route('/profilo/elimina', methods=['POST'])
@login_required
def elimina_account():

    utente = Utente.query.get(current_user.id)
    logout_user() # Rimuove i cookie di sessione dal browser
    GestoreUtente.eliminaProfilo(utente)
    
    flash('Il tuo account è stato rimosso definitivamente dal sistema.', 'info')
    return redirect(url_for('gestione_utente.register'))


@gestione_utente_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_utente.profilo'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            # Il Gestore esegue l'UC-6: Genera e invia la nuova password
            GestoreUtente.recuperaPassword(email)
            flash('Una nuova password è stata generata e inviata al tuo indirizzo email.', 'success')
            return redirect(url_for('gestione_utente.login'))
        except ValueError as e:
            # Caso in cui l'email non esiste
            flash(str(e), 'danger')
            
    return render_template('gestione_utente/forgot_password.html')