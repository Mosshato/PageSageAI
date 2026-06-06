import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv(Path(__file__).resolve().parent / '.env')

def testeaza_conectivitate_gemini():
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Eroare: Nu s-a găsit cheia API.")
        return

    print("🔄 Se inițializează clientul Gemini...")
    # Pasăm cheia explicit ca argument
    client = genai.Client(api_key=api_key)

    print("📡 Se trimite o cerere de test către gemini-1.5-pro...")
    try:
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents='Salut! Spune-mi un singur cuvânt care confirmă că funcționezi.',
        )
        
        print("\n✅ Conexiune reușită!")
        print(f"Răspunsul modelului: {response.text.strip()}")
        
    except errors.APIError as e:
        print(f"\n❌ Eroare API (verifică dacă cheia ta este validă): {e}")
    except Exception as e:
        print(f"\n❌ A apărut o eroare neașteptată: {e}")

if __name__ == "__main__":
    testeaza_conectivitate_gemini()