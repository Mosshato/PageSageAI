import os
import requests
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def creaza_baza_de_date():
    print("1. Se descarcă programa OSSU...")
    url = "https://raw.githubusercontent.com/ossu/computer-science/master/README.md"
    response = requests.get(url)
    if response.status_code != 200:
        print("Eroare la descărcarea fișierului de pe GitHub.")
        return
    
    text_complet = response.text

    print("2. Se izolează cursurile principale (Core Computer Science)...")
    # Extragem textul dintre Core CS și Advanced CS
    pattern = r"(## Core Computer Science.*?)(## Advanced Computer Science)"
    match = re.search(pattern, text_complet, re.DOTALL)

    if not match:
        print("Structura documentului OSSU s-a modificat. Se va folosi tot documentul ca fallback.")
        text_util = text_complet
    else:
        text_util = match.group(1)

    print("3. Se împarte textul în chunk-uri...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700, 
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.create_documents([text_util])
    print(f"Au fost create {len(chunks)} bucăți de text.")

    print("4. Se încarcă modelul de embeddings (Open-Source)...")
    # Folosim un model excelent și lightweight de la HuggingFace (rulează local, e gratuit)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("5. Se inițializează și se salvează ChromaDB local...")
    persist_directory = "./chroma_ossu_db"
    
    # Creăm baza de date și salvăm chunk-urile
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    print(f"Succes! Baza de date a fost salvată în folderul: '{persist_directory}'")

if __name__ == "__main__":
    creaza_baza_de_date()