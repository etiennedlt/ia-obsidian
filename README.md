Ce projet consiste en une application locale développée avec Streamlit et connectée directement à un coffre Obsidian 
afin de centraliser l'interrogation de documents de cours et la gestion de tâches en langage naturel.
Fonctionnant entièrement hors ligne grâce au moteur local Ollama et au modèle Mistral, 
cette solution garantit une totale confidentialité des données sans nécessiter de connexion Internet ni de clés d'API payantes.
L'architecture technique repose sur Python, Streamlit pour l'interface utilisateur,
ainsi que sur des bibliothèques spécialisées pour extraire à la demande le contenu textuel des fichiers Markdown, 
PDF et PowerPoint sélectionnés finement depuis une arborescence interactive. Au-delà de l'analyse documentaire, 
l'application intègre un module de gestion des tâches et du calendrier s'appuyant sur l'horloge système de Windows 
et un traitement algorithmique précis pour planifier, nettoyer et réinitialiser les devoirs 
dans le fichier taches.md du coffre Obsidian. Le démarrage de l'application est optimisé pour être instantané 
grâce à un chargement à la demande des documents, offrant ainsi un espace de travail fluide, rapide 
et entièrement souverain pour l'organisation des études.
