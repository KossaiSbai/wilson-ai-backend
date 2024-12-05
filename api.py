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
        "A termination clause specifies the terms and conditions under which either party may legally "
        "terminate the contract, including scenarios such as material breach, failure to perform obligations, "
        "non-payment, insolvency, or termination for convenience. It outlines the required notice period, "
        "obligations upon termination, and any penalties or liabilities associated with early termination."
    )
  liability_query = (
        "A liability clause delineates the extent of each party's legal responsibilities and obligations within "
        "the contract. It defines the scope of liability for damages, losses, or injuries arising during contract "
        "execution, including limitations of liability, indemnification provisions, exclusions of certain types of "
        "damages, and caps on monetary liabilities to mitigate potential risks."
    )
  indemnification_query = (
        "An indemnification clause outlines the obligations of one party to compensate the other for specified losses, "
        "damages, liabilities, or expenses resulting from certain events or actions, including protection against "
        "third-party claims, breaches of contract, negligence, or misconduct. It specifies the scope, procedures for "
        "claims, and any limitations or exclusions to the indemnifying party's responsibilities."
    )
  confidentiality_query = (
        "A confidentiality clause mandates that the parties protect and refrain from disclosing sensitive, proprietary, "
        "or confidential information obtained during the contract. It defines what constitutes confidential information, "
        "the duration of confidentiality obligations, permitted disclosures, and the consequences of unauthorized "
        "disclosure to safeguard trade secrets, intellectual property, and other private data."
    )
  copyright_query = (
        "A copyright clause specifies the ownership and rights related to the intellectual property created under the contract. "
        "It outlines who retains the copyright, the scope of usage rights granted to each party, any restrictions on the use or "
        "distribution of the copyrighted material, and the duration of these rights. The clause may also address issues such as "
        "the transfer of copyright, licensing terms, moral rights, and obligations to protect the copyrighted work from infringement."
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