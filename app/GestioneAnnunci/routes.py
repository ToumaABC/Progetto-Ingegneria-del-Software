from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.GestioneAnnunci import gestione_annunci_bp


@gestione_annunci_bp.route("/aggiungi_annuncio", methods=["GET", "POST"])
@login_required
def aggiungi_annuncio():
    if current_user.ruolo != "locatore":
        flash("Solo i locatori possono pubblicare annunci.", "danger")
        return redirect(url_for("gestione_annunci.index"))

    if request.method == "POST":
        try:
            current_app.gestore_annunci.aggiungiAnnuncio(
                dati=request.form.to_dict(),
                servizi = request.form.getlist("servizi"),
                file_foto=request.files.getlist("foto"), 
                locatore_id=current_user.id
            )
            flash("Annuncio pubblicato con successo!", "success")
            return redirect(url_for("gestione_annunci.miei_annunci")) # Route da creare per la dashboard locatore
        except ValueError as e:
            flash(str(e), "danger")

    servizi_disponibili = current_app.gestore_annunci.getListaServizi()
    return render_template("gestione_annunci/aggiungi_annuncio.html", servizi=servizi_disponibili)


@gestione_annunci_bp.route("/modifica_annuncio/<int:id>", methods=["GET", "POST"])
@login_required
def modifica_annuncio(id):

    #verifico che l"annuncio esista e l"utente sia il proprietario dell annuncio 
    try:
        annuncio = current_app.gestore_annunci.verificaProprietaAnnuncio(id, current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("gestione_annunci.index"))
    servizi_disponibili = current_app.gestore_annunci.getListaServizi()

    if request.method == "POST":

        # Recupera le foto che l"utente ha spuntato per l"eliminazione
        foto_da_eliminare = request.form.getlist("foto_da_eliminare")
        
        # Recupera le nuove foto caricate 
        nuove_foto = request.files.getlist("nuove_foto")

        try:
            current_app.gestore_annunci.modificaAnnuncio(
                annuncio=annuncio,
                dati=request.form.to_dict(),
                servizi = request.form.getlist("servizi"),
                file_foto=nuove_foto,
                foto_da_eliminare=foto_da_eliminare
            )
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("gestione_annunci/modifica_annuncio.html", annuncio=annuncio, servizi=servizi_disponibili)

        flash("Annuncio modificato con successo.", "success")
        return redirect(url_for("gestione_annunci.miei_annunci"))

    return render_template("gestione_annunci/modifica_annuncio.html", annuncio=annuncio, servizi=servizi_disponibili)


@gestione_annunci_bp.route("/elimina_annuncio/<int:id>", methods=["POST"])
@login_required
def elimina_annuncio(id):
    try:
        current_app.gestore_annunci.eliminaAnnuncio(id,current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("gestione_annunci.miei_annunci"))

    flash("Annuncio eliminato con successo.", "success")
    return redirect(url_for("gestione_annunci.miei_annunci"))

@gestione_annunci_bp.route("/visibilita_annuncio/<int:id>", methods=["POST"])
@login_required
def visibilita_annuncio(id):
    try:
        annuncio = current_app.gestore_annunci.verificaProprietaAnnuncio(id, current_user.id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("gestione_annunci.index"))    
    
    nuovo_stato = current_app.gestore_annunci.cambiaVisibilita(annuncio)
    stato_str = "reso visibile" if nuovo_stato else "nascosto"
    flash(f"L'annuncio è stato {stato_str}.", "info")
        
    return redirect(url_for("gestione_annunci.miei_annunci"))


@gestione_annunci_bp.route("/miei_annunci", methods=["GET"])
@login_required
def miei_annunci():
    if current_user.ruolo != "locatore":
        flash("Accesso consentito solo ai locatori.", "danger")
        return redirect(url_for("gestione_annunci.index"))
    
    return render_template("gestione_annunci/miei_annunci.html", annunci=current_user.annunci)


@gestione_annunci_bp.route("/", methods=["GET"])
@login_required
def index():
    query_testo = request.args.get("query")
    prezzo_max = request.args.get("prezzo_max")
    servizi_selezionati = request.args.getlist("servizi")

    # Chiamiamo la funzione Base del Gestore
    annunci = current_app.gestore_annunci.ricercaAnnunci(query_testo=query_testo, prezzo_max=prezzo_max,
                                                         servizi_selezionati=servizi_selezionati)
    servizi = current_app.gestore_annunci.getListaServizi()
    annunci_salvati_ids=[]
    if current_user.is_authenticated and current_user.ruolo == "studente":
        annunci_salvati_ids = [a.id for a in current_user.getListaAnnunciSalvati()]
    
    return render_template("index.html", annunci=annunci, servizi=servizi, annunci_salvati_ids=annunci_salvati_ids)

@gestione_annunci_bp.route("/annuncio/<int:id>", methods=["GET"])
@login_required
def visualizza_annuncio(id):

    try:
        result = current_app.gestore_annunci.visualizzaAnnuncio(id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for("gestione_annunci.index"))

    puo_recensire = False
    ha_gia_recensito = False

    if current_user.is_authenticated and current_user.ruolo == "studente":
        ha_gia_recensito = current_user.haRecensitoAnnuncio(id)
        puo_recensire = current_user.associato_alla_stanza(id)

    return render_template(
        "gestione_annunci/visualizza_annuncio.html",
        annuncio=result["annuncio"],
        locatore=result["locatore"],
        inquilini_associati=result["inquilini"],
        recensioni=result["recensioni"],
        media_voto=result["media_voto"],
        puo_recensire=puo_recensire,
        ha_gia_recensito=ha_gia_recensito,
    )

@gestione_annunci_bp.route("/salva_annuncio/<int:id>", methods=["POST"])
@login_required
def salva_annuncio(id):
    if current_user.ruolo != "studente":
        flash("Solo gli studenti possono salvare gli annunci.", "danger")
        return redirect(request.referrer or url_for("gestione_annunci.index"))
    
    try:
        current_app.gestore_annunci.salvaAnnuncio(studente_id=current_user.id, annuncio_id=id)
        flash("Annuncio salvato nei preferiti!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    finally:        
        return redirect(request.referrer or url_for("gestione_annunci.index"))


@gestione_annunci_bp.route("/rimuovi_salvato/<int:id>", methods=["POST"])
@login_required
def rimuovi_salvato(id):
    if current_user.ruolo != "studente":
        return redirect(url_for("gestione_annunci.index"))
    
    try:
        current_app.gestore_annunci.eliminaAnnuncioSalvato(studente_id=current_user.id, annuncio_id=id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(request.referrer or url_for("gestione_annunci.annunci_salvati"))

    return redirect(request.referrer or url_for("gestione_annunci.annunci_salvati"))


@gestione_annunci_bp.route("/annunci_salvati", methods=["GET"])
@login_required
def annunci_salvati():
    if current_user.ruolo != "studente":
        flash("Questa sezione è riservata agli studenti.", "danger")
        return redirect(url_for("gestione_annunci.index"))
    
    l_annunci_salvati = current_user.getListaAnnunciSalvati()
    
    annunci_salvati_ids=[]
    if current_user.is_authenticated and current_user.ruolo == "studente":
        annunci_salvati_ids = [a.id for a in l_annunci_salvati]

    return render_template("gestione_annunci/annunci_salvati.html", annunci=l_annunci_salvati, annunci_salvati_ids=annunci_salvati_ids)