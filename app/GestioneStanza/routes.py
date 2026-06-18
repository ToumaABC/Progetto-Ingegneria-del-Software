from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.GestioneStanza import gestione_stanza_bp
from app.GestioneStanza.gestore_stanza import GestoreStanza
from app.GestioneAnnunci.models import AnnuncioStanza



@gestione_stanza_bp.route('/annuncio/<int:id>/associa', methods=['POST'])
@login_required
def associa_studente(id):
    annuncio = AnnuncioStanza.query.get_or_404(id)
    
    if annuncio.locatore_id != current_user.id:
        flash("Non sei autorizzato a modificare questo annuncio.", "danger")
        return redirect(url_for('gestione_annunci.miei_annunci', id=id))

    email = request.form.get('email_studente')
    try:
        GestoreStanza.associaStudente(id, email)
        flash("Studente associato con successo alla stanza!", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('gestione_annunci.miei_annunci', id=id))


@gestione_stanza_bp.route('/annuncio/<int:annuncio_id>/annulla_associazione/<int:studente_id>', methods=['POST'])
@login_required
def annulla_associazione(annuncio_id, studente_id):
    annuncio = AnnuncioStanza.query.get_or_404(annuncio_id)
    
    if annuncio.locatore_id != current_user.id:
        flash("Non sei autorizzato a modificare questo annuncio.", "danger")
        return redirect(url_for('gestione_annunci.miei_annunci'))
        
    try:
        GestoreStanza.annullaAssociazione(annuncio_id, studente_id)
        flash("Studente dissociato con successo dalla stanza.", "success")
    except ValueError as e:
        flash(str(e), "danger")
        
    return redirect(url_for('gestione_annunci.miei_annunci'))