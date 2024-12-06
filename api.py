import os
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend import ClauseType, extract_clauses, process_and_store_document
from fastapi import UploadFile
from db import SQLiteDatabase
from chromadb.utils import embedding_functions
import chromadb

class QueryList(BaseModel):
    queries: List[str]

app = FastAPI()
wilson_ai_db = SQLiteDatabase("wilson.db")
wilson_ai_db.create_file_table()
client = chromadb.PersistentClient(path="./")
EMBED_MODEL = "all-MiniLM-L6-v2"
embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL
)
clauses_collection = client.get_or_create_collection(name="Clauses", embedding_function=embedding_func)

origins = [
    "http://localhost:3000",
    "https://wilson-ai-frontend.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/clauses/{filename}")
def get_clauses(filename: str):
  
    termination_query = (
        "A termination clause defines the grounds and procedures for ending the agreement. It specifies permissible events like breaches, insolvency, "
        "or prolonged force majeure, along with notice requirements. It includes provisions for post-termination obligations, such as returning or destroying "
        "confidential data, and offers remedies like refunds for prepaid but unused services. Certain rights, like data migration assistance, may extend into a "
        "designated transition period to support seamless discontinuation."
    )

    liability_query = (
        "A liability clause sets limits on financial responsibility for damages caused under the contract. It outlines exclusions for indirect, punitive, "
        "or consequential damages, and often caps recoverable amounts to fees paid within a specified period. The clause can provide carve-outs for gross negligence, "
        "breaches of confidentiality, or specific indemnity obligations, ensuring accountability while controlling risk exposure."
    )

    indemnification_query = (
        "An indemnification clause establishes obligations for one party to indemnify the other against potential losses or damages. This includes compensating for "
        "harm arising from contract violations, security breaches, or intellectual property infringement. The clause details procedural steps, such as timely notice "
        "of claims and cooperation in the defense process. It also specifies conditions under which indemnification is excluded, such as unauthorized use or client-provided designs."
    )
    
    confidentiality_query = (
        "A confidentiality clause safeguards sensitive information shared during the agreement. It defines what constitutes confidential information, mandates its secure "
        "handling, and restricts disclosure to authorized individuals. Exceptions may include public domain knowledge or legal obligations. The clause specifies retention periods, "
        "destruction protocols, and equitable remedies like injunctive relief for breaches."
    )

    copyright_query = (
        "A copyright clause delineates intellectual property rights over materials created during the contract. It specifies ownership of pre-existing IP, assigns rights to developed "
        "works, and defines licensing terms for use. The clause includes provisions for protecting proprietary content from misuse and outlines scenarios for transferring rights or "
        "addressing disputes, balancing innovation and ownership."
    )

    termination_clauses = extract_clauses(filename, termination_query, ClauseType.TERMINATION, clauses_collection)
    liability_clauses = extract_clauses(filename, liability_query, ClauseType.LIABILITY, clauses_collection)
    indemnification_clauses = extract_clauses(filename, indemnification_query, ClauseType.INDEMNIFICATION, clauses_collection)
    confidentiality_clauses = extract_clauses(filename, confidentiality_query, ClauseType.CONFIDENTIALITY, clauses_collection)
    copyright_clauses = extract_clauses(filename, copyright_query, ClauseType.COPYRIGHT, clauses_collection)
    return termination_clauses + liability_clauses + indemnification_clauses + confidentiality_clauses + copyright_clauses

TEMP_DIR = "./temp_files" 
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_file(file: UploadFile):
    temp_file_path = os.path.join(TEMP_DIR, file.filename)

    with open(temp_file_path, "wb") as temp_file:
        content = await file.read()
        temp_file.write(content)
    
    print(f"Stored file: {file.filename}")

    try:
        pages = await process_and_store_document(temp_file_path, file.filename, wilson_ai_db, clauses_collection)
        return {"message": "Document parsed successfully", "pages": pages}
    except Exception as e:
        return {"message": "An error occurred during document processing", "error": str(e)}
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

@app.get("/files")
def get_files():
    return wilson_ai_db.get_all_files()