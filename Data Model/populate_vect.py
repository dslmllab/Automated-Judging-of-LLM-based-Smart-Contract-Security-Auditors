

import os
import uuid
import json
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import openai
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ChromaDB Persistent Storage
PERSIST_DIRECTORY = os.environ.get("CHROMA_PERSIST_DIR", "./chroma_data")
OPENAI_API_KEY = "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"


CHUNK_SIZE =500
CHUNK_OVERLAP = 100


# Initialize OpenAI embedding function
try:
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-ada-002"
    )
except Exception as e:
    logger.error(f"Failed to initialize OpenAI embedding function: {e}")
    raise


# Initialize OpenAI embedding function
try:
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name="text-embedding-ada-002"
    )
except Exception as e:
    logger.error(f"Failed to initialize OpenAI embedding function: {e}")
    raise

# Initialize ChromaDB client
try:
    client = chromadb.PersistentClient(
        path=PERSIST_DIRECTORY,
        settings=Settings(anonymized_telemetry=False)
    )
    logger.info(f"ChromaDB client initialized with persist directory: {PERSIST_DIRECTORY}")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB client: {e}")
    raise

# Define collections
COLLECTIONS = {
    "audit_reports": "Audit reports",
    "vulnerabilities": "Known vulnerabilities",
    "security_patterns": "Security patterns and best practices"
}

# Create or load collections
collections = {}
for name, description in COLLECTIONS.items():
    try:
        collections[name] = client.get_collection(name=name, embedding_function=openai_ef)
        logger.info(f"Loaded existing collection: {name}")
        logger.info({collections})
    except Exception as e:
        # Collection doesn't exist, create it
        collections[name] = client.create_collection(
            name=name,
            embedding_function=openai_ef,
            metadata={"description": description}
        )
        logger.info(f"Created new collection: {name}")
    except Exception as e:
        logger.info(f"Error with collection {name}: {e}")
        raise

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into overlapping chunks for better retrieval.

    Args:
        text: The text to split into chunks
        chunk_size: The size of each chunk in characters
        overlap: The overlap between chunks in characters

    Returns:
        List of text chunks
    """
    if not text:
        return []

    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)

    logger.debug(f"Split text into {len(chunks)} chunks")
    return chunks

def add_document_to_collection(
        collection_name: str,
        document_text: str,
        metadata: Optional[Dict] = None,
        document_id: Optional[str] = None
) -> str:
    """
    Adds a document to a ChromaDB collection after chunking.

    Args:
        collection_name: Name of the collection to add to
        document_text: Text content of the document
        metadata: Additional metadata for the document
        document_id: Optional document ID, will generate UUID if not provided

    Returns:
        The document ID

    Raises:
        ValueError: If the collection doesn't exist
    """
    print(collections)
    if collection_name not in collections:
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    collection = collections[collection_name]
    doc_id = document_id or str(uuid.uuid4())

    # Create base metadata if none provided
    meta = metadata.copy() if metadata else {}
    meta["document_id"] = doc_id

    # Split into chunks
    chunks = chunk_text(document_text)

    if not chunks:
        logger.warning(f"No chunks created for document {doc_id}")
        return doc_id

    # Prepare batch data
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}_chunk_{i}"
        chunk_meta = meta.copy()
        chunk_meta.update({
            "chunk_index": i,
            "total_chunks": len(chunks)
        })

        ids.append(chunk_id)
        documents.append(chunk)
        metadatas.append(chunk_meta)

    # Add to collection in batch
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Added document {doc_id} to {collection_name} with {len(chunks)} chunks.")
    except Exception as e:
        logger.error(f"Failed to add document {doc_id} to {collection_name}: {e}")
        raise

    return doc_id

def delete_document(collection_name: str, document_id: str) -> None:
    """
    Deletes a document and all its chunks from a collection.

    Args:
        collection_name: Name of the collection
        document_id: ID of the document to delete
    """
    if collection_name not in collections:
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    collection = collections[collection_name]

    try:
        # Query for all chunks with this document_id
        results = collection.get(
            where={"document_id": document_id}
        )

        if results and results['ids']:
            # Delete the chunks
            collection.delete(ids=results['ids'])
            logger.info(f"Deleted document {document_id} with {len(results['ids'])} chunks from {collection_name}")
        else:
            logger.warning(f"No chunks found for document {document_id} in collection {collection_name}")
    except Exception as e:
        logger.error(f"Error deleting document {document_id} from {collection_name}: {e}")
        raise

def load_and_store_documents(directory: str, collection_name: str, file_extensions: List[str] = [".txt"]) -> int:
    """
    Loads all matching files in a directory and stores them in the vector database.

    Args:
        directory: Path to the directory containing documents
        collection_name: Name of the collection to store in
        file_extensions: List of file extensions to process

    Returns:
        Number of documents processed
    """
    if not os.path.exists(directory):
        logger.error(f"Directory '{directory}' does not exist.")
        return 0

    processed_count = 0

    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)

        if not os.path.isfile(file_path):
            continue

        # Check if the file has a valid extension
        if not any(filename.endswith(ext) for ext in file_extensions):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                document_text = file.read()

            metadata = {
                "filename": filename,
                "source_path": file_path,
                "file_size": os.path.getsize(file_path),
                "last_modified": os.path.getmtime(file_path)
            }

            add_document_to_collection(collection_name, document_text, metadata)
            processed_count += 1

        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8. Trying with latin-1 encoding...")
            try:
                with open(file_path, "r", encoding="latin-1") as file:
                    document_text = file.read()
                add_document_to_collection(collection_name, document_text, {"filename": filename})
                processed_count += 1
            except Exception as e:
                logger.error(f"Failed to process {file_path} with latin-1 encoding: {e}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")

    logger.info(f"Processed {processed_count} documents from {directory} into {collection_name}")
    return processed_count

def query_collection(
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where_filter: Optional[Dict] = None
) -> List[Dict]:
    """
    Query a collection for similar documents.

    Args:
        collection_name: Name of the collection to query
        query_text: The query text
        n_results: Number of results to return
        where_filter: Optional filter to apply

    Returns:
        List of matching documents with their metadata
    """
    if collection_name not in collections:
        raise ValueError(f"Collection '{collection_name}' does not exist.")

    collection = collections[collection_name]

    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )

        # Process results into a more usable format
        processed_results = []
        for i, (doc_id, document, metadata, distance) in enumerate(zip(
                results['ids'][0],
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
        )):
            processed_results.append({
                "id": doc_id,
                "text": document,
                "metadata": metadata,
                "similarity": 1 - distance,  # Convert distance to similarity score
                "rank": i + 1
            })

        return processed_results

    except Exception as e:
        logger.error(f"Error querying collection {collection_name}: {e}")
        raise

# Main execution
if __name__ == "__main__":
    DATA_DIR = os.getenv("DATA_DIR", ".")

    directories = {
        "audit_reports": f"{DATA_DIR}/Audit-Reports",
        "vulnerabilities": f"{DATA_DIR}/Vulnerabilities",
        "security_patterns": f"{DATA_DIR}/scams"
    }

    total_docs = 0

    # Process each directory
    for collection_name, directory in directories.items():
        print('hi')
        try:
            docs_count = load_and_store_documents(
                directory,
                collection_name,
                file_extensions=[".txt", ".md", ".json",".csv","pdf"]
            )
            total_docs += docs_count
        except Exception as e:
            logger.error(f"Failed to process directory {directory}: {e}")

    logger.info(f"Processing complete: added {total_docs} documents")