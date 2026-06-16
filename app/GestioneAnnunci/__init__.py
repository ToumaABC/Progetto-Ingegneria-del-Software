from flask import Blueprint

gestione_annunci_bp = Blueprint('gestione_annunci', __name__)

from app.GestioneAnnunci import routes