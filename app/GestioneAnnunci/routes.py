from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.GestioneAnnunci.gestore_annunci import GestoreAnnunci
from app.GestioneAnnunci.models import AnnuncioStanza, Servizio
from app.GestioneAnnunci import gestione_annunci_bp



@gestione_annunci_bp.route('/aggiungi_annuncio', methods=['GET', 'POST'])
@login_required
def aggiungi_annuncio():
    # Sicurezza: Solo il locatore può aggiungere annunci
    if current_user.ruolo != 'locatore':
        flash('Solo i locatori possono pubblicare annunci.', 'danger')
        return redirect(url_for('gestore_utente.profilo'))

    if request.method == 'POST':
        try:
            # Passiamo il form, la lista delle foto caricate e l'id del locatore al gestore
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
    
    # Recupera tutti gli annunci inseriti dall'utente locatore loggato
    annunci_locatore = AnnuncioStanza.query.filter_by(locatore_id=current_user.id).all()
    return render_template('gestione_annunci/miei_annunci.html', annunci=annunci_locatore)


@gestione_annunci_bp.route('/', methods=['GET'])
@login_required
def index():
    annunci = AnnuncioStanza.query.filter_by(visibile=True).all()

    query_testo = request.args.get('query')
    prezzo_max = request.args.get('prezzo_max')
    
    servizi_selezionati = request.args.getlist('servizi')

    # Chiamiamo la funzione Base del Gestore, passandole anche i filtri estesi
    annunci = GestoreAnnunci.ricerca_annunci(query_testo=query_testo, prezzo_max=prezzo_max, servizi_selezionati=servizi_selezionati)

    servizi = Servizio.query.all()

    return render_template('index.html', annunci=annunci, servizi=servizi)