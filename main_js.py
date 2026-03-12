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
    p = document.createElement("div")
    p.classList.add("log-entry")
    if type == "error":
        p.classList.add("log-error")
    elif type == "success":
        p.classList.add("log-success")

    # Formatage du texte pour éviter l'injection HTML basique
    p.textContent = f"> {message}"
    log_container.appendChild(p)
    # Scroll automatique vers le bas
    log_container.scrollTop = log_container.scrollHeight

async def lancer_analyse(*args):
    # Réinitialiser l'interface
    error_msg.style.display = "none"
    log_container.innerHTML = "" # Vider les logs précédents
    start_btn.disabled = True
    start_btn.textContent = "Traitement en cours..."

    # --- VALIDATION ---
    has_file = file_input.files and file_input.files.length > 0
    has_link = link_input.value.strip() != ""

    if not has_file and not has_link:
        error_msg.style.display = "block"
        log("Erreur : Champs manquants.", "error")
        start_btn.disabled = False
        start_btn.textContent = "Lancer le traitement"
        return

    # --- DÉBUT DU TRAITEMENT ---
    log("Initialisation du traitement...")
    log(f"Fichier sélectionné : {file_input.files[0].name}")
    log(f"Lien de référence : {link_input.value}")

    await asyncio.sleep(1) # Simulation de délai
    log("Lecture du fichier...", "normal")

    # Lecture du fichier (Asynchrone)
    file = file_input.files[0]
    reader = FileReader.new()

    # Création d'une promesse pour attendre la fin de la lecture
    # Note: Dans un vrai cas complexe, on utiliserait asyncio.Future
    # Ici, on utilise une fonction de rappel simple pour la démo

    def on_load(event):
        content = event.target.result
        log(f"Fichier lu avec succès ({len(content)} caractères).", "success")

        log("Connexion simulée au lien distant...")
        # Ici, vous pourriez utiliser js.fetch pour vraiment appeler le lien
        # Pour l'exemple, on simule un traitement sur le contenu
        process_content(content)

    def on_error(event):
        log("Erreur lors de la lecture du fichier.", "error")
        start_btn.disabled = False
        start_btn.textContent = "Lancer le traitement"

    reader.onload = create_proxy(on_load)
    reader.onerror = create_proxy(on_error)
    reader.readAsText(file)

def process_content(content):
    """Simule l'appel à vos classes externes et le traitement."""
    log("Initialisation des classes...", "normal")
    ci = CardImporter()
    ict = ImageCardTransformer()
    pi = PDFImporter()

    # Reset
    ci.delete_pickles()
    ict.delete_images()

    defaut_file = "./files/to_export"

    # Apply
    has_file = file_input.files and file_input.files.length > 0
    has_link = link_input.value.strip() != ""

    if has_link:
        gsci = GoogleSheetsCSVImporter(link_input.value.strip())
        default_csv_filepath = gsci.import_csv()
        ci.parse(default_csv_filepath)
    elif has_file:
        ci.parse(file_input.files)
    ict.transform_cards()
    pdf_filepath = defaut_file+".pdf"
    pi.import_from_images_directory(pdf_filepath=pdf_filepath)

    # Reset
    ci.delete_pickles()
    ict.delete_images()

    log("Analyse terminée avec succès.", "success")
    log("Préparation du fichier de résultat...")

    # Exemple de création de fichier de sortie
    final_result = f"RAPPORT D'ANALYSE\nLien: {link_input.value}\n\n{content.upper()}\n\n[Fin du rapport]"

    blob = Blob.new([final_result], {"type": "text/plain"})
    url = URL.createObjectURL(blob)

    # Création dynamique d'un lien de téléchargement dans les logs
    link_elem = document.createElement("a")
    link_elem.href = url
    link_elem.download = pdf_filepath
    link_elem.textContent = "📥 Télécharger le rapport généré"
    link_elem.style.color = "#3498db"
    link_elem.style.fontWeight = "bold"
    link_elem.style.display = "block"
    link_elem.style.marginTop = "10px"

    log("Traitement complet terminé.", "success")
    log_container.appendChild(link_elem)

    start_btn.disabled = False
    start_btn.textContent = "Lancer le traitement"

# Rendre la fonction accessible globalement
js.lancer_analyse = create_proxy(lancer_analyse)