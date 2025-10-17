from thedebator.retrieval.store import VectorStore
from thedebator.retrieval.types import DocumentChunk


class DummyCollection:
    def __init__(self) -> None:
        self.records = []

    def upsert(self, ids, documents, metadatas):
        self.records.extend(zip(ids, documents, metadatas))

    def query(self, *args, **kwargs):
        query_texts = kwargs.get("query_texts")
        n_results = kwargs.get("n_results")
        if query_texts is None and args:
            query_texts = args[0]
        if n_results is None:
            n_results = args[1] if len(args) > 1 else 3
        _ = query_texts  # unused placeholder
        ids = [[record[0] for record in self.records[:n_results]]]
        documents = [[record[1] for record in self.records[:n_results]]]
        metadatas = [[record[2] for record in self.records[:n_results]]]
        return {"ids": ids, "documents": documents, "metadatas": metadatas}


class DummyClient:
    def __init__(self, collection):
        self.collection = collection

    def get_or_create_collection(self, _name):
        return self.collection

    def delete_collection(self, _name):
        self.collection.records.clear()


def test_vector_store_upsert_and_query(tmp_path):
    store = VectorStore(tmp_path)
    collection = DummyCollection()
    client = DummyClient(collection)

    object.__setattr__(store, "_client", client)

    chunk = DocumentChunk(chunk_id="c1", content="Cell growth increases.", page=5)
    count = store.upsert([chunk])

    assert count == 1

    results = store.similarity_search("cell growth")
    assert results
    assert results[0].page == 5
