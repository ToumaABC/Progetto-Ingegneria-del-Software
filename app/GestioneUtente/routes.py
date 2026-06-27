from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.GestioneUtente import gestione_utente_bp
from app.GestioneUtente.gestore_utente import GestoreUtente



@gestione_utente_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_annunci.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            utente = GestoreUtente.login(email, password)
            login_user(utente)
            return redirect(url_for('gestione_annunci.index'))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('gestione_utente/login.html')


@gestione_utente_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_annunci.index'))
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



@gestione_utente_bp.route('/verify/<token>', methods=['GET'])
def verify_email(token):
    try:
        GestoreUtente.verificaEmail(token)
        flash('Account verificato con successo! Benvenuto in UniAlloggi, ora puoi effettuare il login.', 'success')
        return redirect(url_for('gestione_utente.login'))
    except ValueError as e:
        flash(str(e), 'danger')
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
            flash(str(e), 'danger')
        
    return render_template('gestione_utente/modifica_profilo.html', utente=current_user)


@gestione_utente_bp.route('/profilo/elimina', methods=['POST'])
@login_required
def elimina_account():
    try:
        GestoreUtente.eliminaProfilo(current_user.id)
    except ValueError as e:
        flash(str(e), 'danger')
        return redirect(url_for('gestione_utente.profilo'))
    
    logout_user()
    
    flash('Il tuo account è stato rimosso definitivamente dal sistema.', 'info')
    return redirect(url_for('gestione_utente.register'))


@gestione_utente_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('gestione_utente.profilo'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        try:
            GestoreUtente.recuperaPassword(email)
            flash('Una nuova password è stata generata e inviata al tuo indirizzo email.', 'success')
            return redirect(url_for('gestione_utente.login'))
        except ValueError as e:
            flash(str(e), 'danger')
            
    return render_template('gestione_utente/forgot_password.html')



@gestione_utente_bp.route('/profilo', defaults={'id': None}, methods=['GET'])
@gestione_utente_bp.route('/profilo/<int:id>', methods=['GET'])
@login_required
def profilo(id):

    target_id = id if id is not None else current_user.id
    
    try:
        utente_da_visualizzare = GestoreUtente.visualizzaProfilo(target_id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('gestione_annunci.index'))

    return render_template('gestione_utente/profilo.html', utente=utente_da_visualizzare)