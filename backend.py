from enum import Enum
from typing import List
import uuid
from llama_parse import LlamaParse
from itertools import chain
from db import SQLiteDatabase
from langchain_text_splitters import MarkdownHeaderTextSplitter
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv("LLAMAPARSE_API_KEY")
parser = LlamaParse(api_key=api_key, verbose=True)


class ClauseType(Enum):
    INDEMNIFICATION = "Indemnification"
    TERMINATION = "Termination"
    LIABILITY = "Liability"
    CONFIDENTIALITY = "Confidentiality"
    COPYRIGHT = "Copyright"

async def parse_document_async(document_path: str):
    parsing_output = await parser.aget_json(document_path)
    return parsing_output[0]['pages']

def chunk_with_markdown_splitter(page_md, page_number, file_name: str):
    headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ]
    text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on)
    chunks = text_splitter.split_text(page_md)
    for chunk in chunks:
        chunk.metadata['page_number'] = page_number
        chunk.metadata['file_name'] = file_name
    return chunks    


def store_chunks_in_chroma(chunks: List[any], chroma_collection: any, file_name: str):
    for chunk_index, chunk in enumerate(chunks):
        print("CHUNK ", chunk)
        text = chunk.page_content
        metadata = chunk.metadata

        chroma_collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[f"{file_name}_id_{metadata['page_number']}_{chunk_index}"]
        )

async def process_and_store_document(file_path: str, file_name: str, db: SQLiteDatabase, collection: any):
    if(db.get_file_by_name(file_name)):
        print("File already processed.")
        return
    pages = await parse_document_async(file_path)
    print("Parsed document with", len(pages), "pages.")
    db.add_file((str(uuid.uuid4()), file_name))
    print("Stored file in database.")
    for page in pages:
        chunks = chunk_with_markdown_splitter(page['md'], page['page'], file_name)
        store_chunks_in_chroma(chunks, collection, file_name)


def extract_clauses(file_name: str, query: str, clause_type: ClauseType, collection: any):
    query_texts = [query]
    query_results = collection.query(
        query_texts=query_texts,
        n_results=15,
        include=['embeddings', 'documents', 'metadatas', 'distances'],
        where={"file_name": {"$eq": file_name}}
    )

    print(query_results)

    all_results = list(chain(*query_results['documents']))
    all_metadata = list(chain(*query_results['metadatas']))
    all_distances = list(chain(*query_results['distances']))
    all_ids = list(chain(*query_results['ids']))

    combined_results = [
        {"text": doc, "metadata": meta, "distance": dist, "id": id, "type": clause_type.value}
        for doc, meta, dist, id in zip(all_results, all_metadata, all_distances, all_ids)
    ]
    combined_results = list(filter(lambda x: x['distance'] <= 1.1, combined_results))
    combined_results = sorted(combined_results, key=lambda x: (x['metadata']["page_number"], x['id']))[:5]

    unique_results = {}
    for result in combined_results:
        doc_id = result['id']
        if doc_id not in unique_results:
            unique_results[doc_id] = result

    return list(unique_results.values())