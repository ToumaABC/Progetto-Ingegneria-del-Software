from flask import render_template, request, redirect, url_for, flash,current_app
from flask_login import login_required, current_user
from app.GestioneStanza import gestione_stanza_bp


@gestione_stanza_bp.route('/annuncio/<int:id>/associa', methods=['POST'])
@login_required
def associa_studente(id):
    try:
        current_app.gestore_annunci.verificaProprietaAnnuncio(id,current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('gestione_annunci.miei_annunci'))

    email = request.form.get('email_studente')
    try:
        current_app.gestore_stanza.associaStudente(id, email)
        flash("Studente associato con successo alla stanza!", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('gestione_annunci.miei_annunci', id=id))


@gestione_stanza_bp.route('/annuncio/<int:annuncio_id>/annulla_associazione/<int:studente_id>', methods=['POST'])
@login_required
def annulla_associazione(annuncio_id, studente_id):
    try:
        annuncio = current_app.gestore_annunci.verificaProprietaAnnuncio(annuncio_id, current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('gestione_annunci.miei_annunci'))
    
    if annuncio.locatore_id != current_user.id:
        flash("Non sei autorizzato a modificare questo annuncio.", "danger")
        return redirect(url_for('gestione_annunci.miei_annunci'))
        
    try:
        current_app.gestore_stanza.annullaAssociazione(annuncio_id, studente_id)
        flash("Studente dissociato con successo dalla stanza.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('gestione_annunci.miei_annunci'))



@gestione_stanza_bp.route('/annuncio/<int:annuncio_id>/ticket/nuovo', methods=['GET', 'POST'])
@login_required
def nuovo_ticket(annuncio_id):
    if current_user.ruolo != 'studente':
        flash("Solo gli studenti possono aprire ticket.", "danger")
        return redirect(url_for('gestione_stanza.visualizza_ticket'))

    if request.method == 'POST':
        titolo = request.form.get('titolo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        files = request.files.getlist('foto')

        try:
            current_app.gestore_stanza.nuovoTicket(annuncio_id, current_user.id, titolo, descrizione,files)
            flash("Ticket aperto con successo.", "success")
            return redirect(url_for('gestione_stanza.visualizza_ticket'))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('gestione_stanza/nuovo_ticket.html', annuncio_id=annuncio_id)


@gestione_stanza_bp.route('/ticket/<int:ticket_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_ticket(ticket_id):
    try:
        ticket = current_app.gestore_stanza.verificaProprietaTicket(ticket_id, current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('gestione_stanza.visualizza_ticket'))

    if request.method == "POST":
        titolo = request.form.get("titolo", "").strip()
        descrizione = request.form.get("descrizione", "").strip()
        foto_da_aggiungere = request.files.getlist("foto_nuove")
        foto_da_eliminare = request.form.getlist("foto_da_eliminare")

        try:
            current_app.gestore_stanza.modificaTicket(ticket_id, current_user.id, titolo, descrizione, foto_da_aggiungere, foto_da_eliminare)
            flash("Ticket aggiornato con successo.", "success")
            return redirect(url_for('gestione_stanza.visualizza_ticket'))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('gestione_stanza/modifica_ticket.html', ticket=ticket)


@gestione_stanza_bp.route('/ticket/<int:ticket_id>/elimina', methods=['POST'])
@login_required
def elimina_ticket(ticket_id):
    try:
        current_app.gestore_stanza.eliminaTicket(ticket_id, current_user.id)
        flash("Ticket eliminato.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('gestione_stanza.visualizza_ticket'))


@gestione_stanza_bp.route('/ticket/<int:ticket_id>/avanza', methods=['POST'])
@login_required
def aggiorna_stato_ticket(ticket_id):
    if current_user.ruolo != 'locatore':
        flash("Solo il locatore può aggiornare lo stato del ticket.", "danger")
        return redirect(url_for('gestione_stanza.visualizza_ticket'))

    try:
        current_app.gestore_stanza.aggiornaStatoTicket(ticket_id, current_user.id)
        flash("Stato ticket aggiornato.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('gestione_stanza.visualizza_ticket'))


@gestione_stanza_bp.route('/ticket', methods=['GET'])
@login_required
def visualizza_ticket():
    if current_user.ruolo == 'studente':
        tickets = current_app.gestore_stanza.visualizzaTicketStudente(current_user.id)
        associazione = current_user.getAssociazioneAttiva()
        if associazione :
            annuncio = associazione.annuncio
        else:
            annuncio = None

        return render_template('gestione_stanza/ticket_studente.html',tickets=tickets,annuncio=annuncio)
    else:
        annunci = current_user.annunci
        tickets_per_annuncio = {
            a: current_app.gestore_stanza.visualizzaTicketLocatore(a.id) for a in annunci
        }
        return render_template('gestione_stanza/ticket_locatore.html',
                               tickets_per_annuncio=tickets_per_annuncio)
    

@gestione_stanza_bp.route('/annuncio/<int:annuncio_id>/recensione/nuova', methods=['GET', 'POST'])
@login_required
def nuova_recensione(annuncio_id):
    if current_user.ruolo != 'studente':
        flash("Solo gli studenti possono lasciare recensioni.", "danger")
        return redirect(url_for('gestione_annunci.visualizza_annuncio', id=annuncio_id))

    if request.method == 'POST':
        titolo = request.form.get('titolo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        valutazione = request.form.get('valutazione', '0')

        try:
            current_app.gestore_stanza.aggiungiRecensione(annuncio_id, current_user.id, titolo, descrizione, valutazione)
            flash("Recensione pubblicata con successo.", "success")
            return redirect(url_for('gestione_annunci.visualizza_annuncio', id=annuncio_id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('gestione_stanza/nuova_recensione.html', annuncio_id=annuncio_id)


@gestione_stanza_bp.route('/recensione/<int:recensione_id>/modifica', methods=['GET', 'POST'])
@login_required
def modifica_recensione(recensione_id):
    recensione = current_app.gestore_stanza.getRecensioneById(recensione_id)

    if recensione.associazione.studente_id != current_user.id:
        flash("Non sei autorizzato a visualizzare questa pagina.", "danger")
        return redirect(url_for('gestione_annunci.index'))

    if not recensione:
        flash("Recensione non esistente","danger")
        return redirect(request.referrer or url_for('gestione_annunci.index'))

    if current_user.ruolo != 'studente':
        flash("Non autorizzato.", "danger")
        return redirect(url_for('gestione_annunci.index'))


    if request.method == 'POST':
        titolo = request.form.get('titolo', '').strip()
        descrizione = request.form.get('descrizione', '').strip()
        valutazione = request.form.get('valutazione', '0')

        try:
            recensione = current_app.gestore_stanza.modificaRecensione(recensione_id, current_user.id, titolo, descrizione, valutazione)
            flash("Recensione aggiornata.", "success")
            return redirect(url_for('gestione_annunci.visualizza_annuncio', id=recensione.associazione.annuncio_id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template('gestione_stanza/modifica_recensione.html', recensione=recensione)


@gestione_stanza_bp.route('/recensione/<int:recensione_id>/elimina', methods=['POST'])
@login_required
def elimina_recensione(recensione_id):
    recensione = current_app.gestore_stanza.getRecensioneById(recensione_id)
    if not recensione:
        flash("Recensione non esistente","danger")
        return redirect(request.referrer or url_for('gestione_annunci.index'))

    annuncio_id = recensione.associazione.annuncio_id
    try:
        current_app.gestore_stanza.eliminaRecensione(recensione_id, current_user.id)
        flash("Recensione eliminata.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for('gestione_annunci.visualizza_annuncio', id=annuncio_id))