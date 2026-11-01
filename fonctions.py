import os
import time
from google import genai
from dotenv import load_dotenv
from pypdf import PdfReader
from pptx import Presentation

# Charge les variables secrètes depuis le fichier .env
load_dotenv()

# Récupère la clé de manière sécurisée
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


def lire_notes_obsidian(vault_path):
    """
    Parcourt récursivement le coffre et extrait le texte des fichiers .md, .pdf et .pptx
    """
    notes = []
    if not os.path.exists(vault_path):
        print(f"❌ Le dossier {vault_path} n'existe pas.")
        return notes

    print(f"🔍 Exploration du coffre dans : {vault_path}")

    for root, dirs, files in os.walk(vault_path):
        # Ignore le dossier caché .obsidian
        if ".obsidian" in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            content = ""

            try:
                # Lecture des notes Markdown
                if file.endswith(".md"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                # Lecture des fichiers PDF
                elif file.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            content += extracted + "\n"

                # Lecture des fichiers PowerPoint (.pptx)
                elif file.endswith(".pptx"):
                    prs = Presentation(file_path)
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                for paragraph in shape.text_frame.paragraphs:
                                    content += paragraph.text + "\n"

                # Si du texte a été trouvé, on l'ajoute
                if content.strip():
                    notes.append({
                        "titre": file,
                        "contenu": content
                    })
                    print(f"📄 Document chargé : {file_path}")

            except Exception as e:
                print(f"⚠️ Erreur lors de la lecture de {file}: {e}")

    print(f"✅ Total de documents chargés : {len(notes)}")
    return notes


def poser_question_sur_les_cours(prompt, notes):
    """
    Envoie la question de l'utilisateur ainsi que le contenu de tous les cours à Gemini
    """
    contexte_cours = ""
    for note in notes:
        contexte_cours += f"--- Document : {note['titre']} ---\n{note['contenu']}\n\n"

    prompt_complet = f"""
    Voici le contenu des documents de cours de l'élève (Markdown, PDF, PowerPoint) :
    {contexte_cours}

    En te basant strictement sur ces cours, réponds à la question suivante de l'élève :
    {prompt}
    """

    try:
        debut = time.time()
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt_complet,
        )
        fin = time.time()
        temps_ecoule = round(fin - debut, 2)

        return f"{response.text}\n\n*(Réponse générée en {temps_ecoule} secondes)*"
    except Exception as e:
        return f"Une erreur est survenue lors de la communication avec l'assistant : {e}"