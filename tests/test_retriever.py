import numpy as np
import faiss
import json
from dualgpuopt.rag.retrieve import LegalRetriever

def _dummy_faiss(tmp_path):
    dim = 8
    idx = faiss.IndexFlatIP(dim)
    vecs = np.eye(dim, dtype='float32')
    idx.add(vecs)
    fidx = tmp_path / "mini.faiss"
    faiss.write_index(idx, str(fidx))
    with open(str(fidx)+".meta.json", "w") as fh:
        for i in range(dim):
            fh.write(json.dumps({"id": i, "text": f"doc{i}", "source": "test"})+"\n")
    return fidx

def test_retrieval(tmp_path, monkeypatch):
    fidx = _dummy_faiss(tmp_path)
    # monkey‑patch sentence_transformer.encode to deterministic unit vecs
    import sentence_transformers
    class DummyModel:
        def get_sentence_embedding_dimension(self): 
            return 8
        def encode(self, qs, **k):
            v = np.zeros(8, dtype='float32')
            v[0] = 1.0
            return v
    monkeypatch.setattr(sentence_transformers, "SentenceTransformer",
                        lambda *_a, **_k: DummyModel())
    retr = LegalRetriever(str(fidx))
    res = retr.retrieve("anything", k=2)
    assert len(res) == 1
    assert res[0]["text"] == "doc0"
    assert "citation" in res[0] 