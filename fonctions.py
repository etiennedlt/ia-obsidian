import os
import time
import re
from datetime import datetime, timedelta
import ollama
from pypdf import PdfReader
from pptx import Presentation


def lire_notes_obsidian(vault_path):
    """
    Parcourt récursivement le coffre et extrait le texte des fichiers .md, .pdf et .pptx
    en conservant l'arborescence des dossiers.
    """
    notes = []
    if not os.path.exists(vault_path):
        return notes

    for root, dirs, files in os.walk(vault_path):
        if ".obsidian" in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            content = ""

            try:
                if file.endswith(".md"):
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                elif file.endswith(".pdf"):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            content += extracted + "\n"
                elif file.endswith(".pptx"):
                    prs = Presentation(file_path)
                    for slide in prs.slides:
                        for shape in slide.shapes:
                            if shape.has_text_frame:
                                for paragraph in shape.text_frame.paragraphs:
                                    content += paragraph.text + "\n"

                if content.strip():
                    rel_path = os.path.relpath(file_path, vault_path)
                    dossier = os.path.dirname(rel_path)
                    if not dossier:
                        dossier = "Racine"

                    notes.append({
                        "titre": file,
                        "chemin": rel_path,
                        "dossier": dossier,
                        "contenu": content
                    })
            except Exception as e:
                print(f"⚠️ Erreur lecture {file}: {e}")

    return notes


def poser_question_sur_les_cours(prompt, notes_selectionnees):
    """
    Envoie la question et le contexte des cours sélectionnés à Mistral via Ollama.
    """
    contexte_cours = ""
    for note in notes_selectionnees:
        contexte_cours += f"--- Document : {note['titre']} ({note['chemin']}) ---\n{note['contenu']}\n\n"

    prompt_complet = f"""
    Voici le contenu des documents de cours sélectionnés :
    {contexte_cours}

    En te basant strictement sur ces documents, réponds à la question suivante :
    {prompt}
    """

    try:
        debut = time.time()
        response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt_complet}])
        fin = time.time()
        temps_ecoule = round(fin - debut, 2)
        return f"{response['message']['content']}\n\n*(Réponse générée localement via Ollama en {temps_ecoule} secondes)*"
    except Exception as e:
        return f"Une erreur est survenue avec Ollama : {e}. Vérifiez qu'Ollama est bien lancé."


def interpreter_et_ajouter_taches(vault_path, prompt_utilisateur):
    """
    Utilise la date système Windows et Mistral pour interpréter et structurer les tâches.
    """
    # Calcul précis des 14 prochains jours basé sur l'horloge Windows
    jours_fr = {0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi", 4: "vendredi", 5: "samedi", 6: "dimanche"}
    auj = datetime.now()

    table_calendrier = f"Date système actuelle : {auj.strftime('%d/%m/%Y')}\nCalendrier officiel de référence (utilise ces dates exactes pour les jours mentionnés) :\n"
    for i in range(14):
        d = auj + timedelta(days=i)
        nom_jour = jours_fr[d.weekday()]
        table_calendrier += f"- {nom_jour} -> {d.strftime('%d/%m')}\n"

    prompt_analyse = f"""
    {table_calendrier}

    Instructions strictes :
    Analyse la phrase de l'étudiant et extrait chaque tâche/devoir avec sa date correspondante en te référant UNIQUEMENT à la table ci-dessus. 
    Si une date précise est déjà écrite (ex: 11/11), utilise-la directement.
    N'ajoute aucune condition, aucun texte entre parenthèses, uniquement la date au format [JJ/MM] suivie de la description.

    Phrase : "{prompt_utilisateur}"

    Format de sortie obligatoire (une ligne par tâche, rien d'autre) :
    - [ ] [JJ/MM] Description de la tâche
    """

    try:
        response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt_analyse}])
        taches_formatees = response['message']['content'].strip()

        fichier_taches = os.path.join(vault_path, "taches.md")
        lignes_existantes = []
        if os.path.exists(fichier_taches):
            with open(fichier_taches, "r", encoding="utf-8") as f:
                lignes_existantes = f.readlines()

        contenu_final = "# 📋 Mes Tâches et Calendrier\n\n"

        for ligne in lignes_existantes:
            if ligne.strip().startswith("- [ ]") and "[" in ligne and "]" in ligne:
                contenu_final += ligne.strip() + "\n"

        for ligne in taches_formatees.split("\n"):
            if ligne.strip().startswith("- [ ]"):
                ligne_propre = ligne.strip()
                if not re.search(r'\[\d{2}/\d{2}\]', ligne_propre):
                    ligne_propre = re.sub(r'- \[ \] (\d{2}/\d{2})', r'- [ ] [\1]', ligne_propre)
                contenu_final += ligne_propre + "\n"

        with open(fichier_taches, "w", encoding="utf-8") as f:
            f.write(contenu_final)

        return taches_formatees
    except Exception as e:
        print(f"Erreur IA tâches : {e}")
        return None


def reinitialiser_taches(vault_path):
    """Vide complètement le fichier de tâches."""
    fichier_taches = os.path.join(vault_path, "taches.md")
    try:
        with open(fichier_taches, "w", encoding="utf-8") as f:
            f.write("# 📋 Mes Tâches et Calendrier\n\n*(Calendrier réinitialisé)*\n")
        return True
    except Exception as e:
        return False


def lire_taches_obsidian(vault_path):
    """Lit le contenu du fichier taches.md."""
    fichier_taches = os.path.join(vault_path, "taches.md")
    if not os.path.exists(fichier_taches):
        return "Aucun fichier `taches.md` trouvé."
    with open(fichier_taches, "r", encoding="utf-8") as f:
        return f.read()


def nettoyer_taches_passees(vault_path):
    """Supprime uniquement les tâches dont la date est dépassée par rapport au système."""
    fichier_taches = os.path.join(vault_path, "taches.md")
    if not os.path.exists(fichier_taches):
        return False

    try:
        with open(fichier_taches, "r", encoding="utf-8") as f:
            lignes = f.readlines()

        date_actuelle = datetime.now()
        nouvelles_lignes = ["# 📋 Mes Tâches et Calendrier\n\n"]

        for ligne in lignes:
            if ligne.startswith("- [ ]"):
                match = re.search(r'\[(\d{2})/(\d{2})\]', ligne)
                if match:
                    jour = int(match.group(1))
                    mois = int(match.group(2))
                    annee = date_actuelle.year
                    try:
                        date_tache = datetime(annee, mois, jour)
                        if date_tache >= datetime(date_actuelle.year, date_actuelle.month, date_actuelle.day):
                            nouvelles_lignes.append(ligne)
                    except ValueError:
                        nouvelles_lignes.append(ligne)
                else:
                    nouvelles_lignes.append(ligne)

        with open(fichier_taches, "w", encoding="utf-8") as f:
            f.writelines(nouvelles_lignes)
        return True
    except Exception as e:
        print(f"Erreur nettoyage : {e}")
        return False