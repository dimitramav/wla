# 
# This file provides utilities for managing vector stores using ChromaDB.
#
# Key Features:
# - Configures a persistent ChromaDB client for storing and retrieving embeddings.
# - Defines functions for text splitting, collection management, and embedding generation.
#

# Splitter, embeddings, and Chroma client/collection
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .settings import CHROMA_DIR, EMB_MODEL_ID

# Embeddings: Tiny, CPU-friendly, open-source
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMB_MODEL_ID
)

# Disable Chroma telemetry (prevents those "Failed to send telemetry" logs)
_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=Settings(anonymized_telemetry=False, allow_reset=True)
)

# Creates a text splitter for chunking documents into smaller pieces.
# Parameters:
# - chunk_size: The maximum size of each chunk (default: 800).
# - chunk_overlap: The overlap size between chunks (default: 100).
# Returns:
# - A RecursiveCharacterTextSplitter instance configured with the specified parameters.
def make_splitter(chunk_size: int = 800, chunk_overlap: int = 100):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


# Delete a collection by name
def delete_collection(name: str):
    try:
        _client.delete_collection(name)
    except ValueError:  # Collection doesn't exist
        return False


def collection_name_for(topic: str, emb_model: str = None) -> str:
    """Compute ChromaDB collection name, namespaced by model for non-default models."""
    model = emb_model or EMB_MODEL_ID
    if model != EMB_MODEL_ID:
        slug = model.split("/")[-1].replace("-", "_").replace(".", "_")[:24]
        return f"{topic}__{slug}"
    return topic


# Retrieve or create a collection for a topic
def collection_for(topic: str, emb_model: str = None):
    fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=emb_model) if emb_model else emb_fn
    name = collection_name_for(topic, emb_model)
    return _client.get_or_create_collection(name=name, embedding_function=fn)
