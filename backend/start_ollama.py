#!/usr/bin/env python3
import subprocess
import sys
import time
import os

# Chemin complet vers ollama.exe
OLLAMA_CMD = r"C:\Users\Bellamine Kenza\AppData\Local\Programs\Ollama\ollama.exe"

# Nom du modèle que tu as déjà téléchargé
MODEL_NAME = "deepseek-r1:7b"

def start_ollama():
    """Démarre Ollama si ce n'est pas déjà fait et vérifie le modèle DeepSeek"""
    try:
        # Ajouter Ollama au PATH temporairement (optionnel)
        ollama_dir = os.path.dirname(OLLAMA_CMD)
        os.environ["PATH"] += os.pathsep + ollama_dir

        # Vérifier si Ollama fonctionne
        result = subprocess.run([OLLAMA_CMD, 'list'], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("🚀 Démarrage d'Ollama...")
            subprocess.Popen([OLLAMA_CMD, 'serve'])
            time.sleep(5)
            print("✅ Ollama démarré")
            result = subprocess.run([OLLAMA_CMD, 'list'], capture_output=True, text=True)

        # Vérifier si le modèle DeepSeek est présent
        if MODEL_NAME.lower() not in result.stdout.lower():
            print(f"❌ Le modèle {MODEL_NAME} n'est pas trouvé.")
            print(f"👉 Assurez-vous que {MODEL_NAME} est bien téléchargé via Ollama.")
            return False

        return True

    except FileNotFoundError:
        print("❌ Ollama n'est pas trouvé.")
        print(f"Vérifiez le chemin : {OLLAMA_CMD}")
        print("👉 Installez Ollama si nécessaire: https://ollama.ai")
        return False

if __name__ == "__main__":
    if start_ollama():
        print("✅ Tout est prêt pour l'assistant IA avec DeepSeek!")
        print("👉 Lancez maintenant: python main.py")
    else:
        sys.exit(1)
