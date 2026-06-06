import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.prompts import PromptTemplate

load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# ---------------------------------------------------------------------------
# 1. Incarca DB-ul existent
# ---------------------------------------------------------------------------
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(
    persist_directory="./chroma_ossu_db",
    embedding_function=embeddings
)

retriever = db.as_retriever(search_kwargs={"k": 4})

# ---------------------------------------------------------------------------
# 2. LLM Gemini
# ---------------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.environ['GEMINI_API_KEY'],
    temperature=0.3
)

# ---------------------------------------------------------------------------
# 3. Prompt
# ---------------------------------------------------------------------------
prompt = PromptTemplate.from_template("""You are a helpful assistant with broad general knowledge.

Use the context below if it's relevant to the question.
If the context doesn't help or is insufficient, answer from your own knowledge.
Always mention whether your answer comes from the provided context or your general knowledge.

Context:
{context}

Question: {question}

Answer:""")

# ---------------------------------------------------------------------------
# 4. Chain corect cu RunnableParallel
# ---------------------------------------------------------------------------
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

chain = (
    RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough()
    )
    | prompt
    | llm
    | StrOutputParser()
)

# ---------------------------------------------------------------------------
# 5. Interogare
# ---------------------------------------------------------------------------
question = "What courses cover algorithms?"
print(f"Question: {question}\n")
result = chain.invoke(question)
print(f"Answer: {result}")