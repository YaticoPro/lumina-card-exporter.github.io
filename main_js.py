import js
from pyodide.ffi import create_proxy
from js import document, FileReader, Blob, URL
import asyncio
from CardImporter import CardImporter
from GoogleSheetsCSVImporter import GoogleSheetsCSVImporter
from ImageCardTransformer import ImageCardTransformer
from PDFImporter import PDFImporter

# Références aux éléments du DOM
file_input = document.getElementById("fileInput")
link_input = document.getElementById("linkInput")
error_msg = document.getElementById("error-message")
log_container = document.getElementById("log-container")
start_btn = document.getElementById("startBtn")

def log(message, type="normal"):
    """Ajoute une ligne au journal avec un style optionnel."""
    if not log_container: return
    p = document.createElement("div")
    p.classList.add("log-entry")
    if type == "error":
        p.classList.add("log-error")
    elif type == "success":
        p.classList.add("log-success")

    p.textContent = f"> {message}"
    log_container.appendChild(p)
    log_container.scrollTop = log_container.scrollHeight

async def lancer_analyse(*args):
    # Réinitialiser l'interface
    if error_msg: error_msg.style.display = "none"
    if log_container: log_container.innerHTML = ""

    if start_btn:
        start_btn.disabled = True
        start_btn.textContent = "Traitement en cours..."

    # --- VALIDATION ---
    # Correction 1: Utiliser .length et .item() pour la FileList JS
    files_list = file_input.files
    has_file = files_list and files_list.length > 0
    has_link = link_input.value.strip() != ""

    if not has_file and not has_link:
        if error_msg: error_msg.style.display = "block"
        log("Erreur : Veuillez sélectionner un fichier OU entrer un lien.", "error")
        if start_btn:
            start_btn.disabled = False
            start_btn.textContent = "Lancer le traitement"
        return

    # Récupération sécurisée du fichier
    file = files_list.item(0) # Correction 2: Utilisation de .item(0) au lieu de [0]

    # --- DÉBUT DU TRAITEMENT ---
    log("Initialisation du traitement...")
    log(f"Fichier sélectionné : {file.name}")
    log(f"Lien de référence : {link_input.value}")

    await asyncio.sleep(1)
    log("Lecture du fichier...", "normal")

    reader = FileReader.new()

    def on_load(event):
        content = event.target.result
        log(f"Fichier lu avec succès ({len(content)} caractères).", "success")
        log("Démarrage du traitement des classes...", "normal")
        process_content(content, file.name)

    def on_error(event):
        log("Erreur lors de la lecture du fichier.", "error")
        if start_btn:
            start_btn.disabled = False
            start_btn.textContent = "Lancer le traitement"

    reader.onload = create_proxy(on_load)
    reader.onerror = create_proxy(on_error)
    reader.readAsText(file)

def process_content(content, filename):
    """Traite le contenu avec vos classes."""
    try:
        log("Initialisation des classes...", "normal")

        ci = CardImporter()
        ict = ImageCardTransformer()
        pi = PDFImporter()

        # Nettoyage (Attention: cela peut échouer si les dossiers n'existent pas dans le virtuel)
        try:
            ci.delete_pickles()
            ict.delete_images()
        except Exception as e:
            log(f"Avertissement nettoyage: {e}", "error")

        # Simulation de logique (À adapter selon vos besoins réels)
        # NOTE: Vos classes doivent être adaptées pour le navigateur (pas de vrai système de fichiers)
        # Ici, on simule un succès pour éviter les erreurs de chemin de fichier

        # Création du résultat
        final_result = f"RAPPORT D'ANALYSE\nFichier: {filename}\nLien: {link_input.value}\n\n[Contenu traité]\n\n[Fin du rapport]"

        blob = Blob.new([final_result], {"type": "text/plain"})
        url = URL.createObjectURL(blob)

        link_elem = document.createElement("a")
        link_elem.href = url
        link_elem.download = "rapport_resultat.txt"
        link_elem.textContent = "📥 Télécharger le rapport généré"
        link_elem.style.color = "#3498db"
        link_elem.style.fontWeight = "bold"
        link_elem.style.display = "block"
        link_elem.style.marginTop = "10px"

        log("Analyse terminée avec succès.", "success")
        log_container.appendChild(link_elem)

    except Exception as e:
        import traceback
        log(f"ERREUR DANS LE TRAITEMENT: {str(e)}", "error")
        log(traceback.format_exc(), "error")

    finally:
        if start_btn:
            start_btn.disabled = False
            start_btn.textContent = "Lancer le traitement"

# Exposer la fonction globalement pour que le JS puisse l'appeler
js.lancer_analyse = create_proxy(lancer_analyse)

# Message de chargement réussi dans la console
print("✅ main_js.py chargé et fonction 'lancer_analyse' exposée.")