import streamlit as st
import os
from fonctions import lire_notes_obsidian, poser_question_sur_les_cours

# Configuration de la page
st.set_page_config(page_title="Assistant Obsidian", page_icon="📚", layout="centered")

st.title("🎓 Mon Assistant Cours & Obsidian")
st.write("Posez vos questions sur vos cours synchronisés !")

# Chemin vers votre coffre Obsidian
OBSIDIAN_VAULT_PATH = r"C:\cours\cours"

# Chargement des notes et documents (Markdown, PDF, PPTX)
notes = lire_notes_obsidian(OBSIDIAN_VAULT_PATH)
st.sidebar.success(f"{len(notes)} documents chargés depuis le coffre.")

# Initialisation de l'historique du chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage des anciens messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie utilisateur en bas de page
if prompt := st.chat_input("Posez une question sur vos cours..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyse de vos cours en cours..."):
            reponse = poser_question_sur_les_cours(prompt, notes)
            st.markdown(reponse)

    st.session_state.messages.append({"role": "assistant", "content": reponse})