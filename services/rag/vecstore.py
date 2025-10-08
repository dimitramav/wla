# Splitter, embeddings, and Chroma client/collection
import chromadb
from chromadb.utils import embedding_functions
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .settings import CHROMA_DIR, EMB_MODEL_ID

def make_splitter(chunk_size: int = 800, chunk_overlap: int = 100):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

# Embeddings: Tiny, CPU-friendly, open-source
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMB_MODEL_ID
)

# Disable Chroma telemetry (prevents those "Failed to send telemetry" logs)
_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR),
    settings=Settings(anonymized_telemetry=False, allow_reset=True)
)

def collection_for(lesson: str):
    # single collection per lesson; namespace with a prefix if you like
    return _client.get_or_create_collection(
        name=f"lesson__{lesson}",
        embedding_function=emb_fn
)
