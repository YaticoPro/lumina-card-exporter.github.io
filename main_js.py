# main_js.py
import js
from pyodide.ffi import create_proxy
from js import document, FileReader, Blob, URL, Uint8Array
import asyncio
import os
from zipfile import ZipFile

# DOM Elements
file_input = document.getElementById("fileInput")
link_input = document.getElementById("linkInput")
log_container = document.getElementById("log-container")
start_btn = document.getElementById("startBtn")
pdf_check = document.getElementById("pdf-check")
image_check = document.getElementById("image-check")

def log(msg, type="normal"):
    p = document.createElement("div")
    p.textContent = f"> {msg}"
    if type == "error": p.classList.add("log-error")
    elif type == "success": p.classList.add("log-success")
    log_container.appendChild(p)
    log_container.scrollTop = log_container.scrollHeight

async def lancer_analyse(*args):
    log_container.innerText = ""
    log("🚀 Démarrage du traitement...")
    start_btn.disabled = True
    start_btn.textContent = "Traitement en cours"

    files_list = file_input.files
    link = link_input.value.strip() if link_input else ""
    if files_list and files_list.length == 1:
        file_obj = files_list.item(0)
        user_filename = file_obj.name
        log(f"📄 Fichier sélectionné : {user_filename}", "success")

        # Lire et écrire (Binaire)
        try:
            # Lecture du contenu binaire
            reader = FileReader.new()
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            def on_load(event):
                # Le résultat est dans event.target.result (un ArrayBuffer)
                result = event.target.result
                try:
                    # Pyodide convertit automatiquement ArrayBuffer en bytes via to_py()
                    bytes_data = result.to_py()
                    future.set_result(bytes_data)
                except Exception as e:
                    future.set_exception(e)

            def on_error(event):
                future.set_exception(Exception("Erreur de lecture FileReader"))

            reader.onload = create_proxy(on_load)
            reader.onerror = create_proxy(on_error)

            # Lancer la lecture asynchrone
            reader.readAsArrayBuffer(file_obj)

            # Attendre que la lecture soit finie
            bytes_data = await future

            # Écriture du fichier
            with open(user_filename, "wb") as f:
                f.write(bytes_data)

            log(f"✅ Fichier '{user_filename}' importé avec succès ({len(bytes_data)} octets).", "success")


        except Exception as e:
            log(f"❌ Erreur lors de la lecture du fichier : {e}", "error")
            start_btn.disabled = False
            start_btn.textContent = "Lancer le traitement"
            return

    elif link != "":
        user_filename = "to_export.csv"
        log(f"🌐 Source : Lien distant '{link}'", "success")
        log("⏳ Téléchargement du fichier distant...", "normal")

        # On génère un nom de fichier par défaut pour le virtuel
        if link.lower().endswith(".csv"):
            user_filename = link.split("/")[-1]
        elif link.lower().endswith(".json"):
            user_filename = link.split("/")[-1]

        try:
            from js import fetch as js_fetch

            response = await js_fetch(link)

            if not response.ok:
                raise Exception(f"Erreur HTTP {response.status}")

            # Récupération du contenu binaire (arrayBuffer)
            array_buffer = await response.arrayBuffer()

            # Conversion en bytes Python
            bytes_data = Uint8Array.new(array_buffer).to_py()

            # Écriture dans le virtuel
            with open(user_filename, "wb") as f:
                f.write(bytes_data)

            log(f"✅ Fichier distant téléchargé : '{user_filename}' ({len(bytes_data)} octets).", "success")
            # file_obj =

        except Exception as e:
            log(f"❌ Erreur lors du téléchargement du lien : {e}", "error")
            log("Vérifiez que le lien est accessible (CORS) et valide.", "error")
            start_btn.disabled = False
            start_btn.textContent = "Lancer le traitement"
            return
    else:
        log("Aucun fichier ou lien trouvé", "error")

    log("✅ Tous les fichiers (Système + Utilisateur) sont réunis dans le dossier virtuel.")

    try:
        log("🔧 Importation des cartes...")
        ci = CardImporter()
        ci.parse(user_filename)

        nb_files = 0
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith('.pickle') and not file.startswith('.'):
                    nb_files += 1
        log(f"✅ Cartes importées : {nb_files}", "success")

        log("🎨 Transformation des images...")
        ict = ImageCardTransformer()
        ict.transform_cards()

        if pdf_check.checked:
            log("📄 Génération du PDF...")
            pi = PDFImporter()
            pi.import_from_images_directory(pdf_filepath="resultat.pdf")

        if image_check.checked:
            log("🗂️ Génération du Zip...")
            with ZipFile("resultat.zip", 'w') as zip_file:
                cards_paths = os.listdir(ict.image_directory)
                for card_path in cards_paths:
                    zip_file.write(os.path.join(ict.image_directory, card_path))
                if pdf_check.checked:
                    zip_file.write("resultat.pdf")

        log("🧹 Nettoyage des fichiers temporaires...")

        # Reset
        ci.delete_pickles()
        ict.delete_images()

        # 4. Proposer le téléchargement
        pdf_bytes_python = None
        if os.path.exists("resultat.zip"):
            with open("resultat.zip", "rb") as f:
                pdf_bytes_python = f.read()
        elif os.path.exists("resultat.pdf"):
            with open("resultat.pdf", "rb") as f:
                pdf_bytes_python = f.read()

        if pdf_bytes_python is not None:
            # 2. CONVERSION CRUCIALE : Python bytes -> JS Uint8Array
            # Pyodide fournit un utilitaire pour cela
            try:
                # Conversion directe en tableau d'octets JS
                js_uint8array = Uint8Array.new(pdf_bytes_python)

                # On crée le Blob avec le tableau JS (et non l'objet Python)
                blob = Blob.new([js_uint8array], {"type": "application/pdf"})

            except Exception as conv_err:
                log(f"⚠️ Erreur de conversion binaire : {conv_err}", "error")
                # Fallback : essayer directement (moins fiable mais parfois ça passe)
                blob = Blob.new([pdf_bytes_python], {"type": "application/pdf"})

            # 3. Création du lien de téléchagement
            url = URL.createObjectURL(blob)

            link = document.createElement("a")
            link.href = url
            if image_check.checked:
                link.download = "resultat.zip"
            else:
                link.download = "resultat.pdf"
            link.textContent = "📥 Télécharger le résultat"
            link.style.color = "#3498db"
            link.style.display = "block"
            link.style.marginTop = "10px"

            log("✅ Traitement terminé avec succès !")
            log_container.appendChild(link)
        else:
            log("⚠️ Aucun fichier n'a pas été généré.", "error")

    except Exception as e:
        import traceback
        log(f"❌ Erreur durant le traitement : {e}", "error")
        log(traceback.format_exc(), "error")

    finally:
        start_btn.disabled = False
        start_btn.textContent = "Lancer le traitement"
        os.chdir("/") # Retour à la racine

try:
    # On crée le proxy
    proxy_func = create_proxy(lancer_analyse)
    # On l'assigne dans le namespace global de JS via l'objet js
    js.lancer_analyse = proxy_func
    print("✅ SUCCÈS: Fonction 'lancer_analyse' exportée vers JavaScript.")
except Exception as e:
    print(f"❌ ÉCHEC EXPORT: Impossible d'exposer la fonction : {e}")
    # En cas d'erreur, on la lance dans le global Python pour débogage
    globals()['lancer_analyse'] = lancer_analyse