from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def verifica_continut_db():
    persist_directory = "./chroma_ossu_db"
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Încărcăm baza de date
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    
    # Extragem toate datele brute salvate în Chroma
    date_brute = db.get()
    
    # 1. Verificăm numărul total de chunk-uri stocate
    total_chunks = len(date_brute['ids'])
    print(f"=== VERIFICARE BAZĂ DE DATE ===")
    print(f"Număr total de chunk-uri stocate în DB: {total_chunks}")
    
    if total_chunks == 0:
        print("Baza de date este goală!")
        return

    # 2. Afișăm primele câteva caractere din primele 3 chunk-uri pentru inspectare vizuală
    print("\n=== INSPECTARE FRAGMENTE TEXT (Primele 3 chunk-uri) ===")
    for i in range(min(3, total_chunks)):
        print(f"\n[Chunk {i+1}]:")
        # Luăm textul brut al chunk-ului respectiv
        text_fragment = date_brute['documents'][i]
        # Afișăm primele 250 de caractere din el
        print(text_fragment[:250].replace('\n', ' ') + "...")
        print("-" * 50)

    # 3. Verificăm dacă există cuvinte cheie specifice cursurilor de bază
    cuvinte_cheie = ["Algorithms", "Calculus", "Systems", "Programming"]
    print("\n=== VERIFICARE CONȚINUT TEMATIC ===")
    text_complet_db = " ".join(date_brute['documents'])
    
    for cuvant in cuvinte_cheie:
        contine = cuvant.lower() in text_complet_db.lower()
        status = "✅ Găsit" if contine else "❌ Negăsit"
        print(f"Cursuri/Termeni despre '{cuvant}': {status}")

if __name__ == "__main__":
    verifica_continut_db()