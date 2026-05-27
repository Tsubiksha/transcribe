import chromadb
from app.core.config import settings

client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_PATH)

collection = client.get_or_create_collection(
    name=settings.CHROMA_COLLECTION_NAME
)