from functools import wraps
from flask import current_app, flash, redirect, url_for,request
from flask_login import current_user

def ruolo_richiesto(*ruoli_ammessi):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.ruolo not in ruoli_ammessi:
                flash("Non sei autorizzato ad accedere a questa sezione.", "danger")
                return redirect(url_for("gestione_annunci.index"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def verifica_proprieta_annuncio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        annuncio_id = kwargs.get('id') or kwargs.get('annuncio_id')

        try:
            # Effettua il controllo ed estrae l'annuncio dal database
            annuncio = current_app.gestore_annunci.verificaProprietaAnnuncio(annuncio_id, current_user.id)

            kwargs['annuncio'] = annuncio

        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("gestione_annunci.index"))

        return f(*args, **kwargs)

    return decorated_function


def verifica_proprieta_ticket(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ticket_id = kwargs.get('ticket_id')
        try:
            ticket = current_app.gestore_stanza.verificaProprietaTicket(ticket_id, current_user.id)
            kwargs['ticket'] = ticket
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(url_for("gestione_stanza.visualizza_ticket"))
        return f(*args, **kwargs)
    return decorated_function


def verifica_proprieta_recensione(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        recensione_id = kwargs.get('recensione_id')
        try:
            recensione = current_app.gestore_stanza.verificaProprietaRecensione(recensione_id, current_user.id)
            kwargs['recensione'] = recensione
        except ValueError as e:
            flash(str(e), "danger")
            return redirect(request.referrer or url_for("gestione_annunci.index"))
        return f(*args, **kwargs)
    return decorated_function

