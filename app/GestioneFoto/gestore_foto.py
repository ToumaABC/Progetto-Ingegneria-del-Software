import os
from flask import current_app
from app import db

class GestoreFoto:
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in GestoreFoto.ALLOWED_EXTENSIONS

    @staticmethod
    def salva_file_fisico(file, sotto_cartella, prefisso_nome, id_entita):
        if not file or file.filename == '':
            return None
            
        if not GestoreFoto.allowed_file(file.filename):
            raise ValueError(f"Formato file non supportato. Usa: {GestoreFoto.ALLOWED_EXTENSIONS}")

        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', sotto_cartella)
        os.makedirs(upload_folder, exist_ok=True)

        estensione = file.filename.rsplit('.', 1)[1].lower()
        counter = 1
        
        # Genera il nome formattato
        filename = f"{prefisso_nome}_{id_entita}_foto_{counter}.{estensione}"
        filepath = os.path.join(upload_folder, filename)

        # Cerca il primo nome progressivo libero
        while os.path.exists(filepath):
            counter += 1
            filename = f"{prefisso_nome}_{id_entita}_foto_{counter}.{estensione}"
            filepath = os.path.join(upload_folder, filename)

        # Salva fisicamente il file sul disco
        file.save(filepath)
        
        return f"uploads/{sotto_cartella}/{filename}"

    @staticmethod
    def elimina_file_fisico(percorso_relativo):
        """Elimina il file fisico dal disco del server."""
        if not percorso_relativo:
            return
            
        percorso_assoluto = os.path.join(current_app.root_path, 'static', percorso_relativo)
        if os.path.exists(percorso_assoluto):
            try:
                os.remove(percorso_assoluto)
            except Exception as e:
                print(f"Errore eliminazione file fisico: {e}")

    @staticmethod
    def elimina_foto_db(foto_obj):
        if foto_obj and hasattr(foto_obj, 'percorso_file'):
            # 1. Elimina il file fisico
            GestoreFoto.elimina_file_fisico(foto_obj.percorso_file)
            
            # 2. Elimina il record dal Database
            db.session.delete(foto_obj)