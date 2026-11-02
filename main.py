import streamlit as st
import os
from fonctions import (
    lire_notes_obsidian,
    poser_question_sur_les_cours,
    interpreter_et_ajouter_taches,
    reinitialiser_taches,
    lire_taches_obsidian,
    nettoyer_taches_passees
)

# Configuration de la page Streamlit
st.set_page_config(page_title="Assistant Obsidian Local", page_icon="📚", layout="centered")

st.title("🎓 Mon Assistant Cours & Obsidian")
st.write("Interrogez vos cours et gérez vos tâches 100% en local avec Ollama !")

OBSIDIAN_VAULT_PATH = r"C:\cours\cours"


# --- CHARGEMENT MIS EN CACHE ---
@st.cache_data(show_spinner="⏳ Chargement et lecture de vos cours en cours...")
def charger_tous_les_documents(vault_path):
    return lire_notes_obsidian(vault_path)


tous_les_documents = charger_tous_les_documents(OBSIDIAN_VAULT_PATH)

# --- BARRE LATÉRALE : Arborescence interactive ---
st.sidebar.header("⚙️ Arborescence des Cours")
st.sidebar.success(f"{len(tous_les_documents)} documents chargés au total.")

dossiers_dict = {}
for doc in tous_les_documents:
    dossier = doc["dossier"]
    if dossier not in dossiers_dict:
        dossiers_dict[dossier] = []
    dossiers_dict[dossier].append(doc)

fichiers_selectionnes = []

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Vos Dossiers & Fichiers")

for dossier in sorted(dossiers_dict.keys()):
    with st.sidebar.expander(f"📁 {dossier} ({len(dossiers_dict[dossier])})"):
        tout_cocher_dossier = st.checkbox(f"Tout sélectionner dans {dossier}", value=False, key=f"all_{dossier}")

        for doc in dossiers_dict[dossier]:
            est_coche = st.checkbox(
                doc["titre"],
                value=tout_cocher_dossier,
                key=f"file_{doc['chemin']}"
            )
            if est_coche or tout_cocher_dossier:
                fichiers_selectionnes.append(doc["chemin"])

fichiers_selectionnes = list(set(fichiers_selectionnes))
notes_actives = [doc for doc in tous_les_documents if doc["chemin"] in fichiers_selectionnes]

st.sidebar.markdown("---")
st.sidebar.info(f"🎯 **{len(notes_actives)}** documents actifs pour l'IA.")

# --- SECTION : Gestion du Calendrier et des Tâches ---
st.sidebar.markdown("---")
st.sidebar.subheader("📌 Gestion des Tâches (`taches.md`)")

nouvelle_tache = st.sidebar.text_input("Nouvelle tâche / Rappel :")
if st.sidebar.button("Ajouter la tâche"):
    if nouvelle_tache:
        if interpreter_et_ajouter_taches(OBSIDIAN_VAULT_PATH, nouvelle_tache):
            st.sidebar.success("Tâche ajoutée !")
        else:
            st.sidebar.error("Erreur d'écriture.")
    else:
        st.sidebar.warning("Écrivez une tâche.")

if st.sidebar.button("🧹 Nettoyer les anciennes tâches"):
    if nettoyer_taches_passees(OBSIDIAN_VAULT_PATH):
        st.sidebar.success("Tâches passées purgées !")
    else:
        st.sidebar.error("Erreur lors du nettoyage.")

# --- INTERFACE DE CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez une question sur vos cours ou demandez vos tâches..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Réflexion de l'IA (Mistral)..."):
            p_lower = prompt.lower()
            mots_cles_taches = ["tache", "tâche", "taches", "tâches", "devoir", "devoirs", "planning", "calendrier",
                                "faire", "travail", "rappel", "rappels", "agenda", "todo", "rien"]

            # 1. Suppression / Réinitialisation globale
            if any(mot in p_lower for mot in ["supprime", "vide", "efface", "nettoie"]) and any(
                    mot in p_lower for mot in mots_cles_taches + ["tout"]):
                if reinitialiser_taches(OBSIDIAN_VAULT_PATH):
                    reponse = "🗑️ C'est fait ! Toutes les tâches ont été supprimées et le fichier a été réinitialisé."
                else:
                    reponse = "❌ Erreur lors de la réinitialisation."

            # 2. Ajout de tâches en langage naturel
            elif any(mot in p_lower for mot in ["ajoute", "rajoute", "mets", "note"]) and any(
                    mot in p_lower for mot in mots_cles_taches):
                resultat_ia = interpreter_et_ajouter_taches(OBSIDIAN_VAULT_PATH, prompt)
                if resultat_ia:
                    reponse = f"✅ C'est compris ! L'IA a converti et structuré ces tâches avec leurs dates :\n\n{resultat_ia}"
                else:
                    reponse = "❌ Oups, une erreur est survenue lors de l'analyse."

            # 3. Consultation des tâches
            elif any(mot in p_lower for mot in mots_cles_taches):
                reponse = f"Voici vos tâches actuelles dans Obsidian :\n\n{lire_taches_obsidian(OBSIDIAN_VAULT_PATH)}"

            # 4. Interrogation des cours sélectionnés
            else:
                if not notes_actives:
                    reponse = "⚠️ Aucun document n'est sélectionné dans la barre latérale. Veuillez déplier un dossier et en cocher au moins un pour que je puisse vous répondre !"
                else:
                    reponse = poser_question_sur_les_cours(prompt, notes_actives)

            st.markdown(reponse)

    st.session_state.messages.append({"role": "assistant", "content": reponse})