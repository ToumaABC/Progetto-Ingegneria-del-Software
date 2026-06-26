from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.GestioneAnnunci.gestore_annunci import GestoreAnnunci
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio, AnnuncioSalvato
from app.GestioneAnnunci import gestione_annunci_bp
from app.GestioneStanza.gestore_stanza import GestoreStanza
from app.GestioneUtente.gestore_utente import GestoreUtente
from app.GestioneStanza.gestore_stanza import GestoreStanza



@gestione_annunci_bp.route('/aggiungi_annuncio', methods=['GET', 'POST'])
@login_required
def aggiungi_annuncio():
    if current_user.ruolo != 'locatore':
        flash('Solo i locatori possono pubblicare annunci.', 'danger')
        return redirect(url_for('gestione_annunci.index'))

    if request.method == 'POST':
        try:
            GestoreAnnunci.aggiungiAnnuncio(
                dati_form=request.form, 
                file_foto=request.files.getlist('foto'), 
                locatore_id=current_user.id
            )
            flash('Annuncio pubblicato con successo!', 'success')
            return redirect(url_for('gestione_annunci.miei_annunci')) # Route da creare per la dashboard locatore
        except ValueError as e:
            flash(str(e), 'danger')

    servizi_disponibili = Servizio.query.all()
    return render_template('gestione_annunci/aggiungi_annuncio.html', servizi=servizi_disponibili)


@gestione_annunci_bp.route('/modifica_annuncio/<int:id>', methods=['GET', 'POST'])
@login_required
def modifica_annuncio(id):
    annuncio = AnnuncioStanza.query.get_or_404(id)
    
    # Controllo autorizzazione: il locatore può modificare solo i SUOI annunci
    if annuncio.locatore_id != current_user.id:
        flash('Azione non autorizzata.', 'danger')
        return redirect(url_for('gestione_annunci.index'))

    if request.method == 'POST':
        # Recupera le foto che l'utente ha spuntato per l'eliminazione
        foto_da_eliminare = request.form.getlist('foto_da_eliminare')
        
        # Recupera le nuove foto caricate (se ci sono)
        nuove_foto = request.files.getlist('nuove_foto')

        # Passiamo tutto al Gestore
        GestoreAnnunci.modificaAnnuncio(
            annuncio=annuncio, 
            dati_form=request.form,
            file_foto=nuove_foto,
            foto_da_eliminare=foto_da_eliminare
        )
        
        flash('Annuncio modificato con successo.', 'success')
        return redirect(url_for('gestione_annunci.miei_annunci'))

    servizi_disponibili = Servizio.query.all()
    return render_template('gestione_annunci/modifica_annuncio.html', annuncio=annuncio, servizi=servizi_disponibili)


@gestione_annunci_bp.route('/elimina_annuncio/<int:id>', methods=['POST'])
@login_required
def elimina_annuncio(id):
    annuncio = AnnuncioStanza.query.get_or_404(id)
    
    if annuncio.locatore_id == current_user.id:
        GestoreAnnunci.eliminaAnnuncio(annuncio)
        flash('Annuncio eliminato definitivamente.', 'success')
    else:
        flash('Azione non autorizzata.', 'danger')
        
    return redirect(url_for('gestione_annunci.miei_annunci'))


@gestione_annunci_bp.route('/visibilita_annuncio/<int:id>', methods=['POST'])
@login_required
def visibilita_annuncio(id):
    annuncio = AnnuncioStanza.query.get_or_404(id)
    
    if annuncio.locatore_id == current_user.id:
        nuovo_stato = GestoreAnnunci.cambiaVisibilita(annuncio)
        stato_str = "reso visibile" if nuovo_stato else "nascosto"
        flash(f'L\'annuncio è stato {stato_str}.', 'info')
    else:
        flash('Azione non autorizzata.', 'danger')
        
    return redirect(url_for('gestione_annunci.miei_annunci'))


@gestione_annunci_bp.route('/miei_annunci', methods=['GET'])
@login_required
def miei_annunci():
    if current_user.ruolo != 'locatore':
        flash('Accesso consentito solo ai locatori.', 'danger')
        return redirect(url_for('index'))
    
    annunci_locatore = AnnuncioStanza.query.filter_by(locatore_id=current_user.id).all()
    return render_template('gestione_annunci/miei_annunci.html', annunci=annunci_locatore)


@gestione_annunci_bp.route('/', methods=['GET'])
@login_required
def index():
    query_testo = request.args.get('query')
    prezzo_max = request.args.get('prezzo_max')
    servizi_selezionati = request.args.getlist('servizi')

    # Chiamiamo la funzione Base del Gestore
    annunci = GestoreAnnunci.ricerca_annunci(query_testo=query_testo, prezzo_max=prezzo_max, servizi_selezionati=servizi_selezionati)
    servizi = Servizio.query.all()

    #Aggiungimento Qiao: Prepariamo la lista con gli ID degli annunci salvati
    annunci_salvati_ids = []
    if current_user.is_authenticated and current_user.ruolo == 'studente':
        salvataggi = AnnuncioSalvato.query.filter_by(studente_id=current_user.id).all()
        annunci_salvati_ids = [s.annuncio_id for s in salvataggi]

    return render_template('index.html', annunci=annunci, servizi=servizi, annunci_salvati_ids=annunci_salvati_ids)

@gestione_annunci_bp.route('/annuncio/<int:id>', methods=['GET'])
@login_required
def visualizza_annuncio(id):

    annuncio = AnnuncioStanza.query.filter_by(id=id,visibile=True).first_or_404()
    locatore = GestoreUtente.visualizzaProfilo(annuncio.locatore_id)
    inquilini_associati = GestoreStanza.visualizzaInquilini(id)
    recensioni = GestoreStanza.visualizzaRecensioni(id)
    media_voto = GestoreStanza.calcolaValutazioneMedia(id)

    puo_recensire = False
    ha_gia_recensito = False

    if current_user.is_authenticated and current_user.ruolo == 'studente':
        associazione = GestoreStanza.get_associazione_attiva(id, current_user.id)
        if associazione:
            ha_gia_recensito = associazione.recensione is not None
            puo_recensire = not ha_gia_recensito

    return render_template(
        'gestione_annunci/visualizza_annuncio.html',
        annuncio=annuncio,
        locatore=locatore,
        inquilini_associati=inquilini_associati,
        recensioni=recensioni,
        media_voto=media_voto,
        puo_recensire=puo_recensire,
        ha_gia_recensito=ha_gia_recensito,
    )

@gestione_annunci_bp.route('/salva_annuncio/<int:id>', methods=['POST'])
@login_required
def salva_annuncio(id):
    if current_user.ruolo != 'studente':
        flash('Solo gli studenti possono salvare gli annunci.', 'danger')
        return redirect(request.referrer or url_for('gestione_annunci.index'))
    
    annuncio = AnnuncioStanza.query.filter_by(id=id,visibile=True).first_or_404()
    successo = GestoreAnnunci.salvaAnnuncio(studente_id=current_user.id, annuncio_id=annuncio.id)
    
    if successo:
        flash('Annuncio salvato nei preferiti!', 'success')
    else:
        flash('Hai già salvato questo annuncio.', 'warning')
        
    return redirect(request.referrer or url_for('gestione_annunci.index'))


@gestione_annunci_bp.route('/rimuovi_salvato/<int:id>', methods=['POST'])
@login_required
def rimuovi_salvato(id):
    if current_user.ruolo != 'studente':
        return redirect(url_for('gestione_annunci.index'))
    
    successo = GestoreAnnunci.eliminaAnnuncioSalvato(studente_id=current_user.id, annuncio_id=id)
    
    if successo:
        flash('Annuncio rimosso dai preferiti.', 'success')
        
    return redirect(request.referrer or url_for('gestione_annunci.annunci_salvati'))


@gestione_annunci_bp.route('/annunci_salvati', methods=['GET'])
@login_required
def annunci_salvati():
    if current_user.ruolo != 'studente':
        flash('Questa sezione è riservata agli studenti.', 'danger')
        return redirect(url_for('gestione_annunci.index'))
    
    annunci_preferiti = GestoreAnnunci.getAnnunciSalvati(studente_id=current_user.id)
    
    # AGGIUNTA: Creiamo la lista degli ID per far funzionare la logica dei cuoricini rossi nella card
    annunci_salvati_ids = [annuncio.id for annuncio in annunci_preferiti]
    
    return render_template('gestione_annunci/annunci_salvati.html', annunci=annunci_preferiti, annunci_salvati_ids=annunci_salvati_ids)