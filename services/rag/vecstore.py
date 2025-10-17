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

def make_splitter(chunk_size: int = 800, chunk_overlap: int = 100):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def delete_collection(name: str):
    """Delete a collection by name if it exists.
    
    Args:
        name: Name of the collection to delete
        
    Returns:
        bool: True if collection was deleted, False if it didn't exist
    """
    try:
        _client.delete_collection(name)
    except ValueError:  # Collection doesn't exist
        return False

def collection_for(topic: str):
    # single collection per topic; namespace with a prefix if you like
    return _client.get_or_create_collection(
        name=f"{topic}",
        embedding_function=emb_fn
)
