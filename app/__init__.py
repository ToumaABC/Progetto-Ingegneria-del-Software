import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_login import LoginManager
from flask_mail import Mail



load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Configurazione App & DB da variabili d'ambiente
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.sqlite')
    if test_config:
        app.config.update(test_config)

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # RNF-5: Configurazione Flask-Mail estratta da .env
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from app.GestioneAnnunci.gestore_annunci import GestoreAnnunci
    from app.GestioneStanza.gestore_stanza import GestoreStanza
    from app.GestioneUtente.gestore_utente import GestoreUtente

    gestore_utente = GestoreUtente(db, mail)
    gestore_stanza = GestoreStanza(db)
    gestore_annunci = GestoreAnnunci(db, gestore_stanza)

    app.gestore_utente = gestore_utente
    app.gestore_stanza = gestore_stanza
    app.gestore_annunci = gestore_annunci

    login_manager.login_view = 'gestione_utente.login'

    from app.GestioneUtente import gestione_utente_bp
    from app.GestioneAnnunci import gestione_annunci_bp
    from app.GestioneStanza import gestione_stanza_bp
    app.register_blueprint(gestione_utente_bp)
    app.register_blueprint(gestione_annunci_bp)
    app.register_blueprint(gestione_stanza_bp)

    from app.GestioneUtente.models import Utente
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utente, int(user_id))
    
    login_manager.login_message = "Effettua il login per accedere a questa pagina."
    login_manager.login_message_category = "warning"

    with app.app_context():
        from app.GestioneUtente.models import  Studente, Locatore
        from app.GestioneAnnunci.models import AnnuncioStanza, AnnuncioSalvato, Servizio
        from app.GestioneStanza.models import AssociazioneStudenteStanza, Ticket, StatoTicket, Recensione
        from app.GestioneFoto.models import FotoAnnuncio,FotoTicket, Foto

        db.create_all()

        servizi_default = ["WiFi", "Aria Condizionata", "Lavatrice", "Riscaldamento", "Ascensore", "Posto Auto"]
        
        if not db.session.scalars(select(Servizio)).first():
            for nome in servizi_default:
                nuovo_servizio = Servizio(nome_servizio=nome)
                db.session.add(nuovo_servizio)
            db.session.commit()



    return app


