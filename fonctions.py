import os
import time
import re
from datetime import datetime, timedelta
import ollama
from pypdf import PdfReader
from pptx import Presentation


def lister_arborescence_cours(vault_path):
    notes = []
    if not os.path.exists(vault_path):
        return notes

    for root, dirs, files in os.walk(vault_path):
        if ".obsidian" in root or ".stversions" in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith((".md", ".pdf", ".pptx")):
                rel_path = os.path.relpath(file_path, vault_path)
                dossier = os.path.dirname(rel_path)
                if not dossier:
                    dossier = "Racine"

                notes.append({
                    "titre": file,
                    "chemin": rel_path,
                    "dossier": dossier,
                    "file_path": file_path
                })
    return notes


def charger_contenu_document(file_path):
    content = ""
    try:
        if file_path.endswith(".md"):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif file_path.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    content += extracted + "\n"
        elif file_path.endswith(".pptx"):
            prs = Presentation(file_path)
            for slide in prs.slides:
                for shape in slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            content += paragraph.text + "\n"
    except Exception as e:
        print(f"⚠️ Erreur lecture {file_path}: {e}")
    return content


def poser_question_sur_les_cours(prompt, notes_selectionnees):
    contexte_cours = ""
    for note in notes_selectionnees:
        contenu_texte = charger_contenu_document(note["file_path"])
        contexte_cours += f"--- Document : {note['titre']} ({note['chemin']}) ---\n{contenu_texte}\n\n"

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
        return f"{response['message']['content']}\n\n*(Réponse générée localement en {temps_ecoule} secondes)*"
    except Exception as e:
        return f"Une erreur est survenue avec Ollama : {e}"


def calculer_date_python(expression_jour):
    """
    Calcule mathématiquement la date exacte (JJ/MM) en fonction du jour actuel et de l'expression.
    """
    auj = datetime.now()
    jour_actuel_idx = auj.weekday()  # 0=Lundi, 6=Dimanche

    mapping_jours = {"lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, "vendredi": 4, "samedi": 5, "dimanche": 6}

    expr = expression_jour.lower().strip()
    cible_idx = -1

    for j_nom, j_idx in mapping_jours.items():
        if j_nom in expr:
            cible_idx = j_idx
            break

    if cible_idx == -1:
        return auj.strftime("%d/%m")  # Par défaut aujourd'hui si non trouvé

    # Calcul de base pour trouver le prochain jour correspondant
    jours_a_ajouter = (cible_idx - jour_actuel_idx) % 7
    if jours_a_ajouter == 0:
        jours_a_ajouter = 7  # Si c'est aujourd'hui même, on vise la semaine prochaine par défaut

    # Si l'utilisateur précise explicitement "semaine prochaine" ou "de la semaine prochaine"
    if "semaine prochaine" in expr or "prochain" in expr:
        # Si le jour est déjà passé dans la semaine en cours ou si on veut s'assurer d'être la semaine prochaine
        if "semaine prochaine" in expr and jours_a_ajouter < 7:
            jours_a_ajouter += 7

    date_finale = auj + timedelta(days=jours_a_ajouter)
    return date_finale.strftime("%d/%m")


def interpreter_et_ajouter_taches(vault_path, prompt_utilisateur):
    """
    L'IA extrait uniquement les couples (Jour / Description) et Python calcule les dates mathématiquement.
    """
    prompt_analyse = f"""
    Analyse la phrase de l'étudiant et extrait chaque tâche sous la forme exacte suivante (une par ligne) :
    [EXPRESSION_JOUR] | [DESCRIPTION]

    Exemples d'expressions de jour à extraire : "mardi", "mercredi prochain", "mardi de la semaine prochaine".
    N'ajoute aucun texte superflu, uniquement les lignes au format demandé.

    Phrase : "{prompt_utilisateur}"
    """

    try:
        response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt_analyse}])
        reponse_ia = response['message']['content'].strip()

        taches_formatees = ""
        for ligne in reponse_ia.split("\n"):
            if "|" in ligne:
                parties = ligne.split("|")
                expression_jour = parties[0].strip().replace("-", "").strip()
                description = parties[1].strip()

                # C'est Python qui calcule la vraie date mathématiquement !
                date_calculee = calculer_date_python(expression_jour)
                taches_formatees += f"- [ ] [{date_calculee}] {description}\n"

        fichier_taches = os.path.join(vault_path, "taches.md")
        lignes_existantes = []
        if os.path.exists(fichier_taches):
            with open(fichier_taches, "r", encoding="utf-8") as f:
                lignes_existantes = f.readlines()

        contenu_final = "# 📋 Mes Tâches et Calendrier\n\n"
        for ligne in lignes_existantes:
            if ligne.strip().startswith("- [ ]") and "[" in ligne and "]" in ligne:
                contenu_final += ligne.strip() + "\n"

        contenu_final += taches_formatees

        with open(fichier_taches, "w", encoding="utf-8") as f:
            f.write(contenu_final)

        return taches_formatees.strip()
    except Exception as e:
        print(f"Erreur IA tâches : {e}")
        return None


def reinitialiser_taches(vault_path):
    fichier_taches = os.path.join(vault_path, "taches.md")
    try:
        with open(fichier_taches, "w", encoding="utf-8") as f:
            f.write("# 📋 Mes Tâches et Calendrier\n\n*(Calendrier réinitialisé)*\n")
        return True
    except Exception as e:
        return False


def lire_taches_obsidian(vault_path):
    fichier_taches = os.path.join(vault_path, "taches.md")
    if not os.path.exists(fichier_taches):
        return "Aucun fichier `taches.md` trouvé."
    with open(fichier_taches, "r", encoding="utf-8") as f:
        return f.read()


def nettoyer_taches_passees(vault_path):
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