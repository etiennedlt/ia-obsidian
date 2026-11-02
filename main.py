import streamlit as st
import os
from fonctions import (
    lister_arborescence_cours,
    poser_question_sur_les_cours,
    interpreter_et_ajouter_taches,
    reinitialiser_taches,
    lire_taches_obsidian,
    nettoyer_taches_passees
)

st.set_page_config(page_title="Assistant Obsidian Local", page_icon="📚", layout="centered")

st.title("🎓 Mon Assistant Cours & Obsidian")
st.write("Interrogez vos cours et gérez vos tâches 100% en local avec Ollama !")

OBSIDIAN_VAULT_PATH = r"C:\cours\cours"


@st.cache_data
def charger_arborescence(vault_path):
    return lister_arborescence_cours(vault_path)


tous_les_documents = charger_arborescence(OBSIDIAN_VAULT_PATH)

st.sidebar.header("⚙️ Arborescence des Cours")
st.sidebar.success(f"{len(tous_les_documents)} documents détectés.")

dossiers_dict = {}
for doc in tous_les_documents:
    dossier = doc["dossier"]
    if dossier not in dossiers_dict:
        dossiers_dict[dossier] = []
    dossiers_dict[dossier].append(doc)

fichiers_selectionnes = []

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Vos Dossiers & Fichiers")


def toggle_dossier_callback(dossier_nom):
    all_key = f"all_{dossier_nom}"
    etat_voulu = st.session_state.get(all_key, False)
    for doc in dossiers_dict[dossier_nom]:
        st.session_state[f"file_{doc['chemin']}"] = etat_voulu


for dossier in sorted(dossiers_dict.keys()):
    with st.sidebar.expander(f"📁 {dossier} ({len(dossiers_dict[dossier])})"):
        all_key = f"all_{dossier}"
        st.checkbox(f"Tout sélectionner dans {dossier}", key=all_key, on_change=toggle_dossier_callback,
                    args=(dossier,))

        for doc in dossiers_dict[dossier]:
            file_key = f"file_{doc['chemin']}"
            est_coche = st.checkbox(doc["titre"], key=file_key)
            if est_coche:
                fichiers_selectionnes.append(doc["chemin"])

fichiers_selectionnes = list(set(fichiers_selectionnes))
notes_actives = [doc for doc in tous_les_documents if doc["chemin"] in fichiers_selectionnes]

st.sidebar.markdown("---")
st.sidebar.info(f"🎯 **{len(notes_actives)}** documents actifs.")

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
        with st.spinner("Réflexion de l'IA..."):
            p_lower = prompt.lower()
            mots_cles_taches = ["tache", "tâche", "taches", "tâches", "devoir", "devoirs", "planning", "calendrier",
                                "faire", "travail", "rappel", "rappels", "agenda", "todo", "rien"]

            if any(mot in p_lower for mot in ["supprime", "vide", "efface", "nettoie"]) and any(
                    mot in p_lower for mot in mots_cles_taches + ["tout"]):
                if reinitialiser_taches(OBSIDIAN_VAULT_PATH):
                    reponse = "🗑️ C'est fait ! Toutes les tâches ont été supprimées et le fichier a été réinitialisé."
                else:
                    reponse = "❌ Erreur lors de la réinitialisation."

            elif any(mot in p_lower for mot in ["ajoute", "rajout", "mets", "note"]) and any(
                    mot in p_lower for mot in mots_cles_taches):
                resultat_ia = interpreter_et_ajouter_taches(OBSIDIAN_VAULT_PATH, prompt)
                if resultat_ia:
                    reponse = f"✅ C'est compris ! L'IA a converti et structuré ces tâches avec leurs dates :\n\n{resultat_ia}"
                else:
                    reponse = "❌ Oups, une erreur est survenue lors de l'analyse."

            elif any(mot in p_lower for mot in mots_cles_taches):
                reponse = f"Voici vos tâches actuelles dans Obsidian :\n\n{lire_taches_obsidian(OBSIDIAN_VAULT_PATH)}"

            else:
                if not notes_actives:
                    reponse = "⚠️ Aucun document n'est sélectionné dans la barre latérale. Veuillez déplier un dossier et en cocher au moins un pour que je puisse vous répondre !"
                else:
                    reponse = poser_question_sur_les_cours(prompt, notes_actives)

            st.markdown(reponse)

    st.session_state.messages.append({"role": "assistant", "content": "plus d'erreur si la variable est bien gérée..."})