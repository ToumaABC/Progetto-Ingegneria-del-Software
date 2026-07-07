import os
from flask import current_app
import uuid

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
        filename = f"{prefisso_nome}_{id_entita}_{uuid.uuid4().hex}.{estensione}"
        filepath = os.path.join(upload_folder, filename)

        # Salva fisicamente il file sul disco
        file.save(filepath)
        
        return f"uploads/{sotto_cartella}/{filename}"

    @staticmethod
    def elimina_file_fisico(percorso_relativo):
        if not percorso_relativo:
            return
        percorso_assoluto = os.path.join(current_app.root_path, 'static', percorso_relativo)
        if os.path.exists(percorso_assoluto):
            os.remove(percorso_assoluto)

