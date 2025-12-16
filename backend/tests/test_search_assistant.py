import google.generativeai as genai
import os

def test_gemini_api():
    # Configurer la clé API
    gemini_api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCr3JQvxLSckY2Sph2mOi5f8PbTH9Jk-Tg")
    genai.configure(api_key=gemini_api_key)
    print(f"🔑 Clé API configurée: {gemini_api_key[:10]}...")

    try:
        # Lister les modèles disponibles
        models = genai.list_models()
        print("📋 Modèles Gemini disponibles:")
        for model in models:
            print(f"  - {model.name}")

        # Charger le modèle gemini-pro
        model = genai.GenerativeModel("gemini-pro")
        print(f"✅ Modèle chargé: gemini-pro")

        # Test rapide
        test_prompt = "Salut"
        response = model.generate_content(test_prompt)
        print(f"✅ Test Gemini réussi, réponse:\n{response.output_text}")

    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        print("⚠️ Vérifie ta clé API ou ta connexion")

# Point d'entrée
if __name__ == "__main__":
    test_gemini_api()
