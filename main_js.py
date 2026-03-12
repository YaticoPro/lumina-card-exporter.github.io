# main_js.py
import js
from pyodide.ffi import create_proxy
from js import document, FileReader, Blob, URL, Uint8Array
import asyncio
import os

# Imports (disponibles car chargés par le JS)
from CardImporter import CardImporter
from ImageCardTransformer import ImageCardTransformer
from PDFImporter import PDFImporter
# ... autres imports

# DOM Elements
file_input = document.getElementById("fileInput") # Input avec webkitdirectory
log_container = document.getElementById("log-container")
start_btn = document.getElementById("startBtn")

def log(msg, type="normal"):
    # ... (votre fonction log existante) ...
    p = document.createElement("div")
    p.textContent = f"> {msg}"
    if type == "error": p.classList.add("log-error")
    elif type == "success": p.classList.add("log-success")
    log_container.appendChild(p)
    log_container.scrollTop = log_container.scrollHeight

async def lancer_analyse(*args):
    log("🚀 Démarrage du traitement...")

    # 1. S'assurer qu'on est dans le bon dossier
    # Les fichiers système y sont déjà grâce au JS
    WORK_DIR = "workdir"
    if not os.path.exists(WORK_DIR):
        os.makedirs(WORK_DIR)
    os.chdir(WORK_DIR)
    log(f"📁 Dossier de travail : /{WORK_DIR}")

    # 2. Charger les fichiers UTILISATEUR dans ce même dossier
    files_list = file_input.files
    if not files_list or files_list.length == 0:
        log("⚠️ Aucun fichier utilisateur sélectionné.", "error")
        return

    log(f"📂 {files_list.length} fichiers utilisateur détectés. Importation...")

    for i in range(files_list.length):
        file_obj = files_list.item(i)
        relative_path = file_obj.webkitRelativePath

        # Nettoyer le chemin (retirer le nom du dossier racine sélectionné)
        parts = relative_path.split('/')
        clean_path = '/'.join(parts[1:]) if len(parts) > 1 else relative_path

        # Créer sous-dossiers si besoin
        dir_name = os.path.dirname(clean_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # Lire et écrire (Binaire)
        try:
            array_buffer = file_obj.arrayBuffer()
            bytes_data = Uint8Array.new(array_buffer).to_py()

            with open(clean_path, "wb") as f:
                f.write(bytes_data)
        except Exception as e:
            log(f"Erreur lecture {clean_path}: {e}", "error")

    log("✅ Tous les fichiers (Système + Utilisateur) sont réunis dans le dossier virtuel.")

    # 3. Lancer vos classes
    # Elles vont trouver à la fois les fichiers système (déjà là)
    # et les fichiers utilisateur (qu'on vient de mettre)
    try:
        log("🔧 Initialisation de CardImporter...")
        ci = CardImporter()
        # Adaptez l'argument selon comment votre classe scanne les fichiers
        # Si elle scanne le dossier courant :
        ci.parse(".")

        log("🎨 Transformation des images...")
        ict = ImageCardTransformer()
        ict.transform_cards()

        log("📄 Génération du PDF...")
        pi = PDFImporter()
        pi.import_from_images_directory(pdf_filepath="resultat.pdf")

        # 4. Proposer le téléchargement
        if os.path.exists("resultat.pdf"):
            with open("resultat.pdf", "rb") as f:
                pdf_bytes = f.read()

            blob = Blob.new([pdf_bytes], {"type": "application/pdf"})
            url = URL.createObjectURL(blob)

            link = document.createElement("a")
            link.href = url
            link.download = "resultat.pdf"
            link.textContent = "📥 Télécharger le résultat"
            link.style.color = "#3498db"
            link.style.display = "block"
            link.style.marginTop = "10px"

            log("✅ Traitement terminé avec succès !")
            log_container.appendChild(link)
        else:
            log("⚠️ Le PDF n'a pas été généré.", "error")

    except Exception as e:
        import traceback
        log(f"❌ Erreur durant le traitement : {e}", "error")
        log(traceback.format_exc(), "error")

    finally:
        start_btn.disabled = False
        start_btn.textContent = "Lancer le traitement"
        os.chdir("/") # Retour à la racine

js.lancer_analyse = create_proxy(lancer_analyse)