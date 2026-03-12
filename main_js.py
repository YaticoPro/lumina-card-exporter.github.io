# main_js.py
import js
from pyodide.ffi import create_proxy
from js import document, FileReader, Blob, URL, Uint8Array
import asyncio
import os
import re

# DOM Elements
file_input = document.getElementById("fileInput")
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

    # 2. Charger les fichiers UTILISATEUR dans ce même dossier
    files_list = file_input.files
    if not files_list or files_list.length == 0:
        log("⚠️ Aucun fichier utilisateur sélectionné.", "error")
        return

    if files_list and files_list.length > 0:
        file_obj = files_list.item(0)

        user_filename = file_obj.name

        log(f"📄 Fichier sélectionné : {user_filename}", "success")

        # Lire et écrire (Binaire)
        try:
            log("reading...")
            # Lecture du contenu binaire
            array_buffer = file_obj.arrayBuffer()
            reader = FileReader.new()
            loop = asyncio.get_event_loop()
            future = loop.create_future()

            def on_load(event):
                # Le résultat est dans event.target.result (un ArrayBuffer)
                result = event.target.result
                # Conversion sûre en bytes Python
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
    else:
        log("⚠️ Aucun fichier sélectionné. Le traitement se lancera avec les données par défaut (si disponibles).", "error")
        return

    log("✅ Tous les fichiers (Système + Utilisateur) sont réunis dans le dossier virtuel.")

    # 3. Lancer vos classes
    # Elles vont trouver à la fois les fichiers système (déjà là)
    # et les fichiers utilisateur (qu'on vient de mettre)
    try:
        try:
            from PIL import __version__ as pillow_version
            log(f"🔍 Version de Pillow dans Pyodide : {pillow_version}", "success")
        except Exception as e:
            log(f"Erreur lecture version: {e}", "error")

        log("🔧 Initialisation de CardImporter...")
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

        log("📄 Génération du PDF...")
        pi = PDFImporter()
        pi.import_from_images_directory(pdf_filepath="resultat.pdf")

        # 4. Proposer le téléchargement
        if os.path.exists("resultat.pdf"):
            with open("resultat.pdf", "rb") as f:
                pdf_bytes_python = f.read()

            log(f"📄 PDF généré : {len(pdf_bytes_python)} octets.", "success")

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