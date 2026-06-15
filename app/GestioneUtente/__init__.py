from flask import Blueprint

gestione_utente_bp = Blueprint('gestione_utente', __name__)

from app.GestioneUtente import routes