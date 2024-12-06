# Wilson AI Backend

This repository contains the backend for Wilson AI, a FastAPI-based application for document processing, clause extraction, and storage.

---

## Features

- **Upload Documents:** Upload files for processing and clause extraction.
- **Clause Extraction:** Extract key clauses like Termination, Liability, Indemnification, Confidentiality, and Copyright.
- **File Management:** Retrieve and manage files stored in the database.

---

## Prerequisites

Before running the application, ensure the following are installed:

- Python 3.8 or later
- pip (Python package manager)

---

## Environment Variables

Create a `.env` file in the root directory and include the following variable:

```env
LLAMAPARSE_API_KEY=your_api_key_here
```

Replace `your_api_key_here` with your actual API key for clause processing.

---

## How to Run Locally

1. **Clone the Repository**  
   Clone this repository to your local machine:

   ```bash
   git clone https://github.com/your-repo/wilson-ai-backend.git
   cd wilson-ai-backend
   ```

2. **Install Dependencies**  
   Create a virtual environment and install the required Python packages:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start the Application**  
   Run the FastAPI application:

   ```bash
   fastapi dev api.py
   ```

   The application will be available at `http://localhost:8000`.

---

## Preloaded Databases

This repository includes two preloaded databases to simplify testing and development:

### `wilson.db` (SQLite Database)
- Stores file names and their corresponding IDs.
- Used to keep track of uploaded documents.
- Automatically updated when new files are uploaded via the `/upload/` route.

### `chroma.sqlite3` (ChromaDB Persistent Database)
- Contains embeddings related to several preprocessed legal contracts.
- Preloaded data allows for immediate testing of clause extraction without uploading new files.
- The embeddings are created using the SentenceTransformer model `all-MiniLM-L6-v2`.

These databases ensure you can start testing and exploring the app's functionality right out of the box.


## Routes

### `GET /`
**Description:** Health check endpoint.  
**Response:** `{"Hello": "World"}`  

---

### `GET /clauses/{filename}`
**Description:** Extracts clauses from the specified file.  
**Path Parameter:**
- `filename` (string): Name of the file to extract clauses from.  

**Response:**  
Returns an array of clauses for the file, grouped by types:
- **Termination Clause**
- **Liability Clause**
- **Indemnification Clause**
- **Confidentiality Clause**
- **Copyright Clause**

---

### `POST /upload/`
**Description:** Uploads a document for processing and storage.  
**Request Body:**
- `file` (UploadFile): A file to be uploaded.

**Response:**
- `message`: Status of the upload.
- `pages`: Parsed pages from the document.

The file is temporarily stored in `./temp_files` during processing and removed after processing is completed.

---

### `GET /files`
**Description:** Retrieves all uploaded files from the database.  
**Response:**  
An array of file metadata stored in the database.

---

## Key Libraries Used

- **FastAPI:** High-performance web framework for building APIs.
- **ChromaDB:** Database for managing embeddings and document metadata.
- **SentenceTransformers:** Used for embedding text with the model `all-MiniLM-L6-v2`.

---

## File Structure

```
.
├── backend/                     # Business logic for clause extraction and processing
├── db/                          # Database management utilities
├── main.py                      # Main FastAPI application
├── requirements.txt             # Python dependencies
├── temp_files/                  # Temporary storage for uploaded files
└── .env                         # Environment variables (not included in the repository)
```

---

## Notes

- Ensure `LLAMAPARSE_API_KEY` is added to your `.env` file to enable proper processing of documents.
- Temporary files are deleted after processing.
