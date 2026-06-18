from flask import Blueprint

gestione_stanza_bp = Blueprint('gestione_stanza', __name__)

from app.GestioneStanza import routes