import subprocess
import time

def warmup_phi3():
    """Préchauffe le modèle phi3 pour des réponses plus rapides"""
    print("🔥 Préchargement du modèle phi3...")
    
    try:
        # Lancer une requête simple en background pour charger le modèle
        subprocess.Popen([
            'ollama', 'run', 'phi3',
            'echo', 'loaded'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Attendre un peu
        time.sleep(2)
        print("✅ Modèle phi3 préchargé")
        
    except Exception as e:
        print(f"⚠️ Préchargement échoué: {e}")