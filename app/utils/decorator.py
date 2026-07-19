from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user


def verifica_proprieta_annuncio(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Prende l'id dalla route (es. <int:id> o <int:annuncio_id>)
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