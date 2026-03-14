import os
try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception:
    chromadb = None
    embedding_functions = None

class MemoryManager:
    def __init__(self, persist_directory=None):
        self._fallback_store = {}
        if chromadb is not None and embedding_functions is not None:
            if persist_directory is None:
                persist_directory = os.getenv("CHROMA_DB_PATH", "./chroma_db")
            if not os.path.exists(persist_directory):
                os.makedirs(persist_directory)
            self.client = chromadb.PersistentClient(path=persist_directory)
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            self.collection = self.client.get_or_create_collection(
                name="user_profiles",
                embedding_function=self.embedding_fn
            )
        else:
            self.client = None
            self.collection = None

    def get_user_profile(self, user_id: str) -> str:
        if self.collection is None:
            return self._fallback_store.get(user_id, "")
        try:
            results = self.collection.get(ids=[user_id])
            if results['documents'] and len(results['documents']) > 0:
                return results['documents'][0]
            return ""
        except Exception as e:
            print(f"Error retrieving user profile: {e}")
            return ""

    def update_user_profile(self, user_id: str, profile_text: str):
        if self.collection is None:
            self._fallback_store[user_id] = profile_text
            return True
        try:
            self.collection.upsert(
                documents=[profile_text],
                metadatas=[{"user_id": user_id, "updated_at": "now"}],
                ids=[user_id]
            )
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False

memory_manager = MemoryManager()
